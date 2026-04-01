import asyncio
import json
import os
import pickle
from contextlib import suppress

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

try:
    from .monitor_service import MonitorService
except ImportError:
    from monitor_service import MonitorService


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(REPO_ROOT, "trained_model.pkl")
HISTORICAL_ALERTS_PATH = os.path.join(REPO_ROOT, "k8s_anomaly_alerts.json")

app = FastAPI(title="K8s AIOps Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

monitor_service = MonitorService(model_path=MODEL_PATH)
active_connections = set()
connections_lock = asyncio.Lock()


def load_historical_alerts():
    try:
        with open(HISTORICAL_ALERTS_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def load_model_metadata():
    default_payload = {
        "model_type": None,
        "training_date": None,
        "threshold": None,
        "features": [],
        "auc": None,
        "f1": None,
        "total_features": 0,
    }

    try:
        with open(MODEL_PATH, "rb") as file:
            model_data = pickle.load(file)

        performance = model_data.get("performance") or {}
        features = model_data.get("features") or []

        return {
            "model_type": model_data.get("model_type"),
            "training_date": model_data.get("training_date"),
            "threshold": model_data.get("threshold"),
            "features": features,
            "auc": performance.get("auc"),
            "f1": performance.get("f1"),
            "total_features": len(features),
        }
    except Exception:
        return default_payload


def build_update_payload():
    snapshot = monitor_service.snapshot()
    pods = snapshot["current_pods"]
    total_pods = len(pods)
    anomalies_this_iteration = sum(1 for pod in pods if pod.get("is_anomaly"))
    total_anomalies = len(snapshot["session_alerts"])
    anomaly_rate = (anomalies_this_iteration / total_pods * 100) if total_pods else 0.0

    return {
        "type": "update",
        "iteration": snapshot["iteration"],
        "pods": pods,
        "session_alerts": snapshot["session_alerts"],
        "score_history": snapshot["score_history"],
        "stats": {
            "total_pods": total_pods,
            "anomalies_this_iteration": anomalies_this_iteration,
            "total_anomalies": total_anomalies,
            "anomaly_rate": anomaly_rate,
            "uptime_seconds": snapshot["uptime_seconds"],
        },
    }


async def broadcast_updates():
    while True:
        payload = build_update_payload()

        async with connections_lock:
            connections = list(active_connections)

        stale_connections = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)

        if stale_connections:
            async with connections_lock:
                for websocket in stale_connections:
                    active_connections.discard(websocket)

        await asyncio.sleep(2)


@app.on_event("startup")
async def on_startup():
    monitor_service.start()
    app.state.broadcast_task = asyncio.create_task(broadcast_updates())


@app.on_event("shutdown")
async def on_shutdown():
    monitor_service.stop()

    broadcast_task = getattr(app.state, "broadcast_task", None)
    if broadcast_task:
        broadcast_task.cancel()
        with suppress(asyncio.CancelledError):
            await broadcast_task

    async with connections_lock:
        connections = list(active_connections)
        active_connections.clear()

    for websocket in connections:
        with suppress(Exception):
            await websocket.close()


@app.get("/api/status")
async def get_status():
    snapshot = monitor_service.snapshot()
    return {
        "is_running": snapshot["is_running"],
        "iteration": snapshot["iteration"],
        "uptime_seconds": snapshot["uptime_seconds"],
        "start_time": snapshot["start_time"],
    }


@app.get("/api/pods")
async def get_pods():
    return monitor_service.snapshot()["current_pods"]


@app.get("/api/alerts")
async def get_alerts():
    return monitor_service.snapshot()["session_alerts"]


@app.get("/api/alerts/historical")
async def get_historical_alerts():
    return load_historical_alerts()


@app.get("/api/model")
async def get_model():
    return load_model_metadata()


@app.get("/api/score-history")
async def get_score_history():
    return monitor_service.snapshot()["score_history"]


@app.post("/api/control/stop")
async def stop_monitoring():
    monitor_service.stop()
    snapshot = monitor_service.snapshot()
    return {
        "is_running": snapshot["is_running"],
        "iteration": snapshot["iteration"],
        "uptime_seconds": snapshot["uptime_seconds"],
        "start_time": snapshot["start_time"],
    }


@app.post("/api/control/start")
async def start_monitoring():
    monitor_service.start()
    snapshot = monitor_service.snapshot()
    return {
        "is_running": snapshot["is_running"],
        "iteration": snapshot["iteration"],
        "uptime_seconds": snapshot["uptime_seconds"],
        "start_time": snapshot["start_time"],
    }


@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(build_update_payload())

    async with connections_lock:
        active_connections.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with connections_lock:
            active_connections.discard(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
