"""Smart Discovery Assistant — application entry point."""

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from src.app.dependencies import experiment_service, production_service, ui_service
from src.phase1.api.router import router as phase1_router
from src.phase2.api.router import mount_frontend, router as phase2_router
from src.phase3.api.router import legacy as phase3_legacy_router
from src.phase3.api.router import router as phase3_router
from src.phase4.api.router import router as phase4_router
from src.shared.models.domain import PurchaseRecord
from src.shared.survey.pdf_parser import load_survey_summary

app = FastAPI(
    title="Smart Discovery Assistant",
    description="AI-powered Cross Category Discovery for Swiggy Instamart",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(phase1_router)
app.include_router(phase2_router)
app.include_router(phase3_router)
app.include_router(phase3_legacy_router)
app.include_router(phase4_router)

mount_frontend(app)


class RecommendationRequest(BaseModel):
    user_id: str
    purchase_records: list[PurchaseRecord] = Field(default_factory=list)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "env": settings.app_env,
        "llm_enabled": settings.llm_enabled,
        "continuous_learning": settings.enable_continuous_learning,
        "phases": {
            "1": "ready",
            "2": "ready",
            "3": "ready",
            "4": "ready",
        },
    }


@app.get("/api/v1/survey/summary")
def survey_summary():
    return load_survey_summary().model_dump()


@app.post("/api/v1/recommendations")
def get_recommendation(request: RecommendationRequest):
    """Legacy endpoint — Phase 2 card + Phase 3 A/B split."""
    start = time.perf_counter()
    assignment = experiment_service.assign_variant(request.user_id)
    variant = assignment.variant

    if variant == "control":
        elapsed_ms = (time.perf_counter() - start) * 1000
        production_service.monitor.check_sla_compliance(elapsed_ms)
        return {
            "variant": "control",
            "recommendation": None,
            "message": "Generic 'People also bought' widget (control group)",
            "latency_ms": round(elapsed_ms, 2),
        }

    response = ui_service.get_card_response(
        request.user_id,
        request.purchase_records or None,
        variant="treatment",
    )

    if response.recommendation:
        experiment_service.register_impression(
            request.user_id,
            response.recommendation.recommendation_id,
            response.recommendation.category,
            variant,
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    production_service.monitor.check_sla_compliance(elapsed_ms)

    payload = response.model_dump()
    payload["latency_ms"] = round(elapsed_ms, 2)
    return payload


@app.get("/api/v1/phases")
def list_phases():
    return {
        "phases": [
            {
                "id": 1,
                "name": "Recommendation Engine",
                "status": "complete",
                "path": "src/phase1/",
            },
            {
                "id": 2,
                "name": "UI Integration",
                "status": "complete",
                "path": "src/phase2/",
            },
            {
                "id": 3,
                "name": "A/B Testing & Analytics",
                "status": "complete",
                "path": "src/phase3/",
                "components": [
                    "service.py",
                    "ab_testing/experiment.py",
                    "analytics/dashboard.py",
                    "feedback/collector.py",
                    "api/router.py",
                ],
            },
            {
                "id": 4,
                "name": "Production Rollout",
                "status": "complete",
                "path": "src/phase4/",
                "components": [
                    "service.py",
                    "deployment/config.py",
                    "deployment/kubernetes.py",
                    "monitoring/kpi_monitor.py",
                    "learning/retrainer.py",
                    "api/router.py",
                ],
            },
        ]
    }
