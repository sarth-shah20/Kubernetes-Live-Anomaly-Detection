import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import random
import threading
from datetime import datetime

import numpy as np

from k8s_real_time_monitor import KubernetesRealTimeMonitor


class MonitorService:
    """Thread-safe wrapper around KubernetesRealTimeMonitor for FastAPI."""

    def __init__(self, model_path=None, namespace=None, interval_seconds=10):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = model_path or os.path.join(repo_root, "trained_model.pkl")
        self.namespace = namespace or os.getenv("AIOPS_NAMESPACE", "default")
        self.interval_seconds = interval_seconds

        self.monitor = KubernetesRealTimeMonitor(
            model_path=self.model_path,
            namespace=self.namespace,
        )

        self.is_running = False
        self.iteration = 0
        self.start_time = None
        self.current_pods = []
        self.session_alerts = []
        self.score_history = []

        self._thread = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._last_uptime_seconds = 0.0

    def start(self):
        with self._lock:
            if self.is_running:
                return False

            self._stop_event.clear()
            self.is_running = True
            self.start_time = datetime.now()
            self._last_uptime_seconds = 0.0
            self._thread = threading.Thread(
                target=self._run_monitor_loop,
                daemon=True,
                name="aiops-monitor-thread",
            )
            self._thread.start()
            return True

    def stop(self):
        with self._lock:
            if not self.is_running:
                return False

            self._last_uptime_seconds = self._calculate_uptime_locked()
            self.is_running = False
            self._stop_event.set()
            thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=2)

        return True

    def snapshot(self):
        with self._lock:
            return {
                "is_running": self.is_running,
                "iteration": self.iteration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "current_pods": copy.deepcopy(self.current_pods),
                "session_alerts": copy.deepcopy(self.session_alerts),
                "score_history": copy.deepcopy(self.score_history),
                "uptime_seconds": self._calculate_uptime_locked(),
            }

    def _run_monitor_loop(self):
        while not self._stop_event.is_set():
            iteration_timestamp = datetime.now()
            try:
                raw_metrics = self.monitor.get_cluster_metrics()
                if not raw_metrics:
                    raw_metrics = [self._build_fallback_pod_metrics()]

                pod_results = []
                score_entry = {
                    "timestamp": iteration_timestamp.isoformat(),
                    "pods": {},
                }

                for pod_data in raw_metrics:
                    result = self._analyze_pod(pod_data, iteration_timestamp)
                    pod_results.append(result)
                    score_entry["pods"][result["pod_name"]] = result["anomaly_score"]

                with self._lock:
                    self.iteration += 1
                    self.current_pods = pod_results
                    self.session_alerts = list(reversed(copy.deepcopy(self.monitor.alerts)))
                    self.score_history.append(score_entry)
                    self.score_history = self.score_history[-100:]
            except Exception as exc:
                print(f"⚠️  Monitor service iteration failed: {exc}")

            if self._stop_event.wait(self.interval_seconds):
                break

        with self._lock:
            self.is_running = False
            self._last_uptime_seconds = self._calculate_uptime_locked()

    def _analyze_pod(self, pod_data, timestamp):
        pod_name = pod_data.get("pod_name", "unknown-pod")
        namespace = pod_data.get("namespace") or self.namespace
        features = self.monitor.engineer_features(pod_data)
        is_anomaly, anomaly_score, _confidence = self.monitor.predict_anomaly(features)
        normalized_score = float(max(0.0, min(1.0, anomaly_score)))
        severity = self._severity_for_score(normalized_score)
        recommended_actions = []

        if is_anomaly:
            alert_severity = severity if severity != "normal" else "low"
            alert = self.monitor.create_alert(
                pod_name,
                normalized_score,
                features,
                severity=alert_severity,
            )
            recommended_actions = alert.get("recommended_actions", [])
            severity = alert_severity

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": normalized_score,
            "severity": severity,
            "cpu_usage": float(features.get("cpu_usage_percent", pod_data.get("cpu_usage", 0.0))),
            "memory_usage": float(features.get("memory_usage_percent", pod_data.get("memory_usage", 0.0))),
            "response_time": float(features.get("response_time_ms", 0.0)),
            "error_rate": float(features.get("error_rate_percent", 0.0)),
            "pod_restarts": int(features.get("pod_restarts", pod_data.get("restart_count", 0))),
            "recommended_actions": recommended_actions,
            "timestamp": timestamp.isoformat(),
        }

    def _build_fallback_pod_metrics(self):
        return {
            "pod_name": f"demo-app-{random.randint(1000, 9999)}",
            "namespace": self.namespace,
            "phase": "Running",
            "restart_count": 0,
            "cpu_usage": float(max(0, min(100, np.random.normal(30, 15)))),
            "memory_usage": float(max(0, min(100, np.random.normal(45, 20)))),
            "timestamp": datetime.now(),
        }

    def _severity_for_score(self, score):
        if score >= 0.8:
            return "high"
        if score >= 0.7:
            return "medium"
        if score >= 0.6:
            return "low"
        return "normal"

    def _calculate_uptime_locked(self):
        if not self.start_time:
            return 0.0
        if self.is_running:
            return max(0.0, (datetime.now() - self.start_time).total_seconds())
        return self._last_uptime_seconds
