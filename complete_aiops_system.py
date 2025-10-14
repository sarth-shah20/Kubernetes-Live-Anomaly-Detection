"""
COMPLETE AIOPS SYSTEM FOR KUBERNETES
Train ML models, deploy for real-time monitoring, and detect anomalies

Usage:
    python complete_aiops_system.py --mode train    # Train models
    python complete_aiops_system.py --mode monitor  # Real-time monitoring
    python complete_aiops_system.py --mode full     # Train + Monitor
"""

import sys
import argparse
import pickle
from datetime import datetime

# Import the advanced ML pipeline code
# (Paste the entire advanced ML pipeline class here or import it)
from ml_pipeline import KubernetesAnomalyDetector, main as train_main
from k8s_real_time_monitor import KubernetesRealTimeMonitor


def train_and_save_model():
    """Train the ML model and save for deployment"""
    print("="*80)
    print("PHASE 1: TRAINING ML MODELS")
    print("="*80)
        
    # Initialize and train
    detector = KubernetesAnomalyDetector(contamination=0.12, random_state=42)
    
    # Load data
    X, y = detector.load_and_preprocess_data('kubernetes_metrics_dataset.csv')
    
    # Feature selection
    X_selected, selected_features = detector.feature_selection(X, y, k=15)
    detector.selected_features = selected_features
    
    # Train models
    detector.train_models(X_selected, y)
    
    # Evaluate
    results = detector.evaluate_models()
    
    # Save best model
    best_model_name = max(results.items(), key=lambda x: x[1]['f1'])[0]
    best_model = detector.models[best_model_name]
    
    model_data = {
        'model': best_model,
        'scaler': detector.scaler,
        'features': selected_features,
        'threshold': 0.6,
        'model_type': best_model_name,
        'training_date': datetime.now().isoformat(),
        'performance': results[best_model_name]
    }
    
    with open('trained_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n✅ Model trained and saved!")
    print(f"   Model: {best_model_name}")
    print(f"   F1-Score: {model_data['performance']['f1']:.3f}")
    print(f"   AUC: {model_data['performance']['auc']:.3f}")
    
    return detector


def start_real_time_monitoring():
    """Start real-time Kubernetes monitoring"""
    print("="*80)
    print("PHASE 2: REAL-TIME KUBERNETES MONITORING")
    print("="*80)
    
    
    monitor = KubernetesRealTimeMonitor(
        model_path='trained_model.pkl',
        namespace='default'
    )
    
    print("\n🚀 Starting continuous monitoring...")
    print("   Monitoring interval: 10 seconds")
    print("   Press Ctrl+C to stop\n")
    
    monitor.monitor_continuous(
        interval_seconds=10,
        duration_minutes=0  # Run indefinitely
    )
    
    # Export alerts when stopped
    monitor.export_alerts()


def main():
    parser = argparse.ArgumentParser(description='Complete AIOps System for Kubernetes')
    parser.add_argument('--mode', choices=['train', 'monitor', 'full'], default='full',
                       help='Mode: train (model only), monitor (real-time only), full (both)')
    
    args = parser.parse_args()
    
    print("🚀 KUBERNETES AIOPS - PREDICTIVE ANOMALY DETECTION")
    print("="*80)
    
    if args.mode in ['train', 'full']:
        detector = train_and_save_model()
        
        if args.mode == 'train':
            print("\n✅ Training complete! Run with --mode monitor to start monitoring")
            return
    
    if args.mode in ['monitor', 'full']:
        if args.mode == 'full':
            print("\n" + "="*80)
            input("Press Enter to start real-time monitoring...")
        
        start_real_time_monitoring()


if __name__ == "__main__":
    main()