import pandas as pd
import numpy as np
import pickle
import time
import json
from datetime import datetime
from kubernetes import client, config
import requests
import warnings
warnings.filterwarnings('ignore')

class KubernetesRealTimeMonitor:
    """
    Real-time Kubernetes anomaly detection and monitoring system
    Integrating trained ML models with live Kubernetes metrics
    """
    
    def __init__(self, model_path='trained_model.pkl', namespace='default'):
        """
        Initializing real-time monitoring system
        
        Arguments:
            model_path: Path to trained model pickle file
            namespace: Kubernetes namespace to monitor
        """
        self.namespace = namespace
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.anomaly_threshold = 0.6
        self.alerts = []
        
        # Load trained model
        self.load_model(model_path)
        
        # Initialize Kubernetes client
        try:
            # Try loading in-cluster config first (when running in K8s)
            config.load_incluster_config()
            print("✅ Loaded in-cluster Kubernetes config")
        except:
            # Fall back to local kubeconfig (for local testing)
            try:
                config.load_kube_config()
                print("✅ Loaded local Kubernetes config")
            except Exception as e:
                print(f"⚠️  Could not load Kubernetes config: {e}")
                print("   Running in simulation mode")
        
        self.v1 = client.CoreV1Api()
        self.metrics_api = None
        
    def load_model(self, model_path):
        """Load the trained ML model and preprocessing objects"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['features']
                self.anomaly_threshold = model_data.get('threshold', 0.6)
            print(f"✅ Model loaded from {model_path}")
            print(f"   Features: {len(self.feature_columns)}")
            print(f"   Threshold: {self.anomaly_threshold}")
        except FileNotFoundError:
            print(f"⚠️  Model file not found: {model_path}")
            print("   Will need to train model first")
    
    def get_pod_metrics(self, pod_name):
        """
        Get metrics for a specific pod from Kubernetes
        Returns dict with CPU, memory, network, and other metrics
        """
        try:
            # Get pod info
            pod = self.v1.read_namespaced_pod(pod_name, self.namespace)
            
            # Get pod status
            pod_status = pod.status
            container_statuses = pod_status.container_statuses or []
            
            # Calculate restart count
            restart_count = sum(cs.restart_count for cs in container_statuses)
            
            # Get resource requests/limits
            containers = pod.spec.containers
            total_cpu_request = 0
            total_memory_request = 0
            
            for container in containers:
                if container.resources.requests:
                    cpu_req = container.resources.requests.get('cpu', '0')
                    mem_req = container.resources.requests.get('memory', '0')
                    # Parse CPU (e.g., "100m" = 0.1 cores)
                    total_cpu_request += self._parse_cpu(cpu_req)
                    # Parse memory (e.g., "128Mi")
                    total_memory_request += self._parse_memory(mem_req)
            
            # Get metrics from metrics-server (if available)
            try:
                metrics = self._get_pod_metrics_from_server(pod_name)
            except Exception as e:
                # If metrics-server not available, simulate realistic metrics
                # metrics = self._simulate_pod_metrics()
                print(f"   ⚠️  Metrics-server failed for {pod_name}: {e}")
                metrics = self._simulate_pod_metrics()
            
            return {
                'pod_name': pod_name,
                'namespace': self.namespace,
                'phase': pod_status.phase,
                'restart_count': restart_count,
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'cpu_request': total_cpu_request,
                'memory_request': total_memory_request,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"⚠️  Error getting metrics for {pod_name}: {e}")
            return None
    
    def _parse_cpu(self, cpu_str):
        """Parse Kubernetes CPU format (e.g., '100m', '0.5', '2')"""
        if isinstance(cpu_str, (int, float)):
            return float(cpu_str)
        cpu_str = str(cpu_str)
        if cpu_str.endswith('n'):      # nanocores
            return float(cpu_str[:-1]) / 1e9
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)
    
    def _parse_memory(self, mem_str):
        """Parse Kubernetes memory format (e.g., '128Mi', '1Gi')"""
        if isinstance(mem_str, (int, float)):
            return float(mem_str)
        mem_str = str(mem_str).upper()
        
        units = {
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
            'KI': 1024,
            'MI': 1024**2,
            'GI': 1024**3,
            'TI': 1024**4
        }
        
        for unit, multiplier in units.items():
            if mem_str.endswith(unit):
                return float(mem_str[:-len(unit)]) * multiplier
        
        return float(mem_str)
    
    def _get_pod_metrics_from_server(self, pod_name):
        """Get actual metrics via kubectl proxy at localhost:8001"""
        import requests
        
        url = f"http://localhost:8001/apis/metrics.k8s.io/v1beta1/namespaces/{self.namespace}/pods/{pod_name}"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            raise Exception(f"Metrics server returned {response.status_code}")
        
        data = response.json()
        
        total_cpu_cores = 0
        total_mem_bytes = 0
        
        for container in data.get('containers', []):
            cpu_str = container['usage'].get('cpu', '0')
            mem_str = container['usage'].get('memory', '0')
            total_cpu_cores += self._parse_cpu(cpu_str)
            total_mem_bytes += self._parse_memory(mem_str)
        
        # Convert to percentages (minikube default: 2 cores, 2GB RAM)
        cpu_percent  = min((total_cpu_cores / 2.0) * 100, 100)
        mem_percent  = min((total_mem_bytes / (2 * 1024**3)) * 100, 100)
        
        return {
            'cpu_usage':    round(cpu_percent, 2),
            'memory_usage': round(mem_percent, 2)
        }
    
    def _simulate_pod_metrics(self):
        """Simulate realistic pod metrics for demo purposes"""
        base_cpu = np.random.normal(25, 10)
        base_memory = np.random.normal(40, 15)
        
        return {
            'cpu_usage': max(0, min(100, base_cpu)),
            'memory_usage': max(0, min(100, base_memory))
        }
    
    def get_cluster_metrics(self):
        """
        Get comprehensive metrics for all pods in the namespace
        """
        try:
            pods = self.v1.list_namespaced_pod(self.namespace)
            
            all_metrics = []
            for pod in pods.items:
                pod_name = pod.metadata.name
                metrics = self.get_pod_metrics(pod_name)
                if metrics:
                    all_metrics.append(metrics)
            
            return all_metrics
        except Exception as e:
            print(f"⚠️  Error getting cluster metrics: {e}")
            return []
    
    def engineer_features(self, raw_metrics):
        """
        Transform raw Kubernetes metrics into ML-ready features
        Matches the features used during model training
        """
        features = {}
        
        # Base metrics
        features['cpu_usage_percent'] = raw_metrics.get('cpu_usage', 0)
        features['memory_usage_percent'] = raw_metrics.get('memory_usage', 0)
        features['pod_restarts'] = raw_metrics.get('restart_count', 0)
        
        # Simulated metrics (in production, get from Prometheus)
        features['response_time_ms'] = np.random.normal(150, 50)
        features['error_rate_percent'] = np.random.normal(0.5, 0.2)
        features['network_io_mbps'] = np.random.normal(50, 10)
        features['disk_io_mbps'] = np.random.normal(30, 5)
        
        # Derived features
        features['cpu_memory_ratio'] = features['cpu_usage_percent'] / (features['memory_usage_percent'] + 0.1)
        features['resource_pressure'] = features['cpu_usage_percent'] + features['memory_usage_percent']
        features['performance_score'] = 100 - (features['response_time_ms']/50 + features['error_rate_percent']*10)
        
        # Time-based features
        now = datetime.now()
        features['hour'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        features['is_business_hours'] = 1 if 9 <= now.hour <= 17 else 0
        
        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        features['day_sin'] = np.sin(2 * np.pi * now.weekday() / 7)
        features['day_cos'] = np.cos(2 * np.pi * now.weekday() / 7)
        
        # Interaction features
        features['cpu_memory_product'] = features['cpu_usage_percent'] * features['memory_usage_percent']
        features['response_error_product'] = features['response_time_ms'] * features['error_rate_percent']
        
        return features
    
    def predict_anomaly(self, features):
        """
        Predict if the current metrics indicate an anomaly
        
        Returns:
            tuple: (is_anomaly, anomaly_score, confidence)
        """
        if self.model is None:
            print("⚠️  No model loaded")
            return False, 0.0, 0.0
        
        # Create feature vector in correct order
        feature_vector = []
        for col in self.feature_columns:
            feature_vector.append(features.get(col, 0))
        
        # Convert to numpy array and reshape
        X = np.array(feature_vector).reshape(1, -1)
        
        # Scale features
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Make prediction
        try:
            if hasattr(self.model, 'predict_proba'):
                # For models with probability
                prediction = self.model.predict(X_scaled)[0]
                proba = self.model.predict_proba(X_scaled)[0]
                anomaly_score = proba[1] if len(proba) > 1 else proba[0]
                is_anomaly = prediction == 1
                confidence = max(proba)
            else:
                # For Isolation Forest
                prediction = self.model.predict(X_scaled)[0]
                score = -self.model.score_samples(X_scaled)[0]
                is_anomaly = prediction == -1
                anomaly_score = score
                confidence = min(1.0, score)
            
            return is_anomaly, anomaly_score, confidence
            
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return False, 0.0, 0.0
    
    def create_alert(self, pod_name, anomaly_score, features, severity='medium'):
        """Create an alert for detected anomaly"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'pod_name': pod_name,
            'namespace': self.namespace,
            'severity': severity,
            'anomaly_score': float(anomaly_score),
            'metrics': {
                'cpu_usage': features.get('cpu_usage_percent', 0),
                'memory_usage': features.get('memory_usage_percent', 0),
                'response_time': features.get('response_time_ms', 0),
                'error_rate': features.get('error_rate_percent', 0),
                'pod_restarts': features.get('pod_restarts', 0)
            },
            'recommended_actions': self._get_recommended_actions(features)
        }
        
        self.alerts.append(alert)
        return alert
    
    def _get_recommended_actions(self, features):
        """Generate recommended actions based on anomaly patterns"""
        actions = []
        
        if features.get('cpu_usage_percent', 0) > 80:
            actions.append("Scale up replicas or increase CPU limits")
        
        if features.get('memory_usage_percent', 0) > 80:
            actions.append("Increase memory limits or check for memory leaks")
        
        if features.get('response_time_ms', 0) > 500:
            actions.append("Investigate slow queries or external dependencies")
        
        if features.get('error_rate_percent', 0) > 2:
            actions.append("Check application logs for errors")
        
        if features.get('pod_restarts', 0) > 3:
            actions.append("Investigate crash loops - check liveness/readiness probes")
        
        if not actions:
            actions.append("Monitor closely - multiple metrics showing unusual patterns")
        
        return actions
    
    def monitor_continuous(self, interval_seconds=60, duration_minutes=10):
        """
        Continuously monitor Kubernetes cluster for anomalies
        
        Args:
            interval_seconds: Time between monitoring checks
            duration_minutes: Total monitoring duration (0 = infinite)
        """
        print(f"\n🚀 STARTING REAL-TIME KUBERNETES ANOMALY DETECTION")
        print(f"   Namespace: {self.namespace}")
        print(f"   Interval: {interval_seconds}s")
        print(f"   Duration: {duration_minutes} minutes")
        print("="*70)
        
        start_time = time.time()
        iteration = 0
        total_anomalies = 0
        
        try:
            while True:
                iteration += 1
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"\n[{current_time}] Monitoring Iteration #{iteration}")
                print("-" * 70)
                
                # Get all pod metrics
                pod_metrics = self.get_cluster_metrics()
                
                if not pod_metrics:
                    print("⚠️  No pods found or unable to get metrics")
                    print("   Simulating pod metrics for demo...")
                    # Create simulated pod for demo
                    pod_metrics = [{
                        'pod_name': f'demo-app-{np.random.randint(1000, 9999)}',
                        'namespace': self.namespace,
                        'phase': 'Running',
                        'restart_count': 0,
                        'cpu_usage': np.random.normal(30, 15),
                        'memory_usage': np.random.normal(45, 20),
                        'timestamp': datetime.now()
                    }]
                
                # Analyze each pod
                anomalies_detected = 0
                
                for pod_data in pod_metrics:
                    pod_name = pod_data['pod_name']
                    
                    # Engineer features
                    features = self.engineer_features(pod_data)
                    
                    # Predict anomaly
                    is_anomaly, anomaly_score, confidence = self.predict_anomaly(features)
                    
                    # Display results
                    status_icon = "🚨" if is_anomaly else "✅"
                    status_text = "ANOMALY" if is_anomaly else "NORMAL"
                    
                    print(f"{status_icon} Pod: {pod_name[:40]:<40} | "
                          f"Status: {status_text:<8} | "
                          f"Score: {anomaly_score:.3f} | "
                          f"CPU: {features['cpu_usage_percent']:>5.1f}% | "
                          f"MEM: {features['memory_usage_percent']:>5.1f}%")
                    
                    # Create alert if anomaly detected
                    if is_anomaly:
                        anomalies_detected += 1
                        total_anomalies += 1
                        
                        severity = 'high' if anomaly_score > 0.8 else 'medium'
                        alert = self.create_alert(pod_name, anomaly_score, features, severity)
                        
                        print(f"   ⚠️  ALERT: {severity.upper()} severity")
                        print(f"   📋 Actions: {', '.join(alert['recommended_actions'][:2])}")
                
                # Summary
                print("-" * 70)
                print(f"Summary: {len(pod_metrics)} pods monitored, "
                      f"{anomalies_detected} anomalies detected this iteration")
                print(f"Total anomalies detected: {total_anomalies}")
                
                # Check if duration exceeded
                if duration_minutes > 0:
                    elapsed_minutes = (time.time() - start_time) / 60
                    if elapsed_minutes >= duration_minutes:
                        print(f"\n✅ Monitoring completed ({duration_minutes} minutes)")
                        break
                
                # Wait for next iteration
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped by user")
        
        # Print final summary
        self.print_monitoring_summary(iteration, total_anomalies)
    
    def print_monitoring_summary(self, iterations, total_anomalies):
        """Print summary of monitoring session"""
        print("\n" + "="*70)
        print("📊 MONITORING SESSION SUMMARY")
        print("="*70)
        print(f"Total iterations: {iterations}")
        print(f"Total anomalies detected: {total_anomalies}")
        print(f"Anomaly rate: {(total_anomalies/iterations)*100:.1f}%")
        print(f"Alerts generated: {len(self.alerts)}")
        
        if self.alerts:
            print(f"\n🚨 Recent Alerts:")
            for alert in self.alerts[-5:]:  # Show last 5 alerts
                print(f"   [{alert['timestamp']}] {alert['pod_name']}")
                print(f"      Severity: {alert['severity'].upper()} | Score: {alert['anomaly_score']:.3f}")
                print(f"      CPU: {alert['metrics']['cpu_usage']:.1f}% | "
                      f"Memory: {alert['metrics']['memory_usage']:.1f}%")
        
        print("="*70)
    
    def export_alerts(self, filename='k8s_anomaly_alerts.json'):
        """Export alerts to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.alerts, f, indent=2, default=str)
        print(f"✅ Alerts exported to {filename}")


def save_model_for_deployment(detector, filename='trained_model.pkl'):
    """
    Save trained model and preprocessing objects for real-time deployment
    
    Args:
        detector: Trained KubernetesAnomalyDetector instance
        filename: Output pickle file name
    """
    # Get best model
    best_model_name = max(detector.results.items(), key=lambda x: x[1]['f1'])[0]
    best_model = detector.models[best_model_name]
    
    model_data = {
        'model': best_model,
        'scaler': detector.scaler,
        'features': detector.selected_features if hasattr(detector, 'selected_features') else detector.feature_columns,
        'threshold': 0.6,
        'model_type': best_model_name,
        'training_date': datetime.now().isoformat(),
        'performance': detector.results[best_model_name]
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"✅ Model saved to {filename}")
    print(f"   Model type: {best_model_name}")
    print(f"   Features: {len(model_data['features'])}")
    print(f"   F1-Score: {model_data['performance']['f1']:.3f}")
    
    return filename


# Demo function
def demo_real_time_monitoring():
    """
    Demonstration of real-time Kubernetes monitoring
    """
    print("🎯 KUBERNETES REAL-TIME ANOMALY DETECTION DEMO")
    print("="*70)
    
    # Check if model exists
    import os
    if not os.path.exists('trained_model.pkl'):
        print("⚠️  Model not found. Please run training pipeline first:")
        print("   1. Run: python ml_pipeline_advanced.py")
        print("   2. This will create trained_model.pkl")
        print("   3. Then run this script again")
        return
    
    # Initialize monitor
    monitor = KubernetesRealTimeMonitor(
        model_path='trained_model.pkl',
        namespace='default'  # Change to your namespace
    )
    
    # Start continuous monitoring
    print("\n📡 Starting continuous monitoring...")
    print("   Press Ctrl+C to stop\n")
    
    monitor.monitor_continuous(
        interval_seconds=10,  # Check every 10 seconds
        duration_minutes=5    # Run for 5 minutes (0 = infinite)
    )
    
    # Export alerts
    monitor.export_alerts()


if __name__ == "__main__":
    demo_real_time_monitoring()