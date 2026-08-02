"""Phase 4 REST API — deployment, monitoring, continuous learning."""

from fastapi import APIRouter

from src.app.dependencies import production_service

router = APIRouter(prefix="/api/v1/phase4", tags=["Phase 4 — Production"])


@router.get("/health")
def phase4_health():
    return {
        "phase": 4,
        "status": "ready",
        "components": [
            "service.py",
            "deployment/config.py",
            "deployment/kubernetes.py",
            "monitoring/kpi_monitor.py",
            "learning/retrainer.py",
        ],
    }


@router.get("/deployment/spec")
def deployment_spec():
    return production_service.get_deployment_spec().model_dump()


@router.get("/deployment/kubernetes")
def kubernetes_manifests():
    return production_service.get_kubernetes_manifests()


@router.get("/monitoring/status")
def monitoring_status(last_latency_ms: float | None = None):
    return production_service.get_monitoring_status(last_latency_ms).model_dump()


@router.get("/monitoring/alerts")
def alert_history(limit: int = 20):
    return {"alerts": production_service.monitor.get_alert_history(limit)}


@router.get("/learning/status")
def learning_status():
    return production_service.get_learning_status()


@router.post("/learning/retrain")
def trigger_retrain(force: bool = False):
    return production_service.run_learning_cycle(force=force)
