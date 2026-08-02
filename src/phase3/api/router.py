"""Phase 3 REST API — A/B testing, analytics dashboard, feedback."""

from fastapi import APIRouter

from src.app.dependencies import discovery_pipeline, experiment_service
from src.phase3.schemas import FeedbackRequest

router = APIRouter(prefix="/api/v1/phase3", tags=["Phase 3 — Experimentation"])

legacy = APIRouter(prefix="/api/v1", tags=["Phase 3 — Legacy Routes"])


@router.get("/health")
def phase3_health():
    return {
        "phase": 3,
        "status": "ready",
        "components": [
            "service.py",
            "ab_testing/experiment.py",
            "analytics/dashboard.py",
            "feedback/collector.py",
            "api/router.py",
        ],
    }


@router.get("/ab-test/assign/{user_id}")
def assign_variant(user_id: str):
    return experiment_service.assign_variant(user_id).model_dump()


@router.get("/ab-test/results")
def ab_test_results():
    return experiment_service.get_ab_results()


@router.get("/analytics/dashboard")
def analytics_dashboard():
    return experiment_service.get_dashboard().model_dump()


@router.get("/analytics/kpis")
def kpi_summary():
    return experiment_service.analytics.get_kpi_summary()


@router.get("/analytics/impressions")
def impression_log(limit: int = 50):
    return {"impressions": experiment_service.analytics.get_impression_log(limit)}


@router.get("/feedback/summary")
def feedback_summary():
    return experiment_service.feedback.get_summary()


@router.post("/feedback")
def submit_feedback_phase3(request: FeedbackRequest):
    return experiment_service.process_feedback(request)


@legacy.post("/feedback")
def submit_feedback_legacy(request: FeedbackRequest):
    return experiment_service.process_feedback(request)


@legacy.get("/analytics/kpis")
def kpis_legacy():
    return experiment_service.analytics.get_kpi_summary()


@legacy.get("/analytics/ab-test")
def ab_test_legacy():
    return experiment_service.get_ab_results()


@legacy.post("/model/train")
def train_model_legacy():
    metadata = discovery_pipeline.train()
    return {"status": "trained", "metadata": metadata}
