"""Phase 1 REST API — purchase analysis, recommendation, model training."""

from fastapi import APIRouter

from src.phase1.pipeline import DiscoveryPipeline
from src.phase1.schemas import AnalyzeHistoryRequest, TrainModelRequest

router = APIRouter(prefix="/api/v1/phase1", tags=["Phase 1 — Recommendation Engine"])

pipeline = DiscoveryPipeline()


@router.get("/health")
def phase1_health():
    return {
        "phase": 1,
        "status": "ready",
        "components": [
            "purchase_history/analyzer",
            "recommendation_engine/engine",
            "models/trainer",
            "pipeline",
        ],
    }


@router.post("/analyze")
def analyze_purchase_history(request: AnalyzeHistoryRequest):
    """Step 1: Analyze purchase history (FR1 repetitive buyer detection)."""
    report = pipeline.analyze(request.user_id, request.purchase_records or None)
    return report.model_dump()


@router.post("/recommend")
def recommend_category(request: AnalyzeHistoryRequest):
    """Step 2–3: Score candidates and return exactly one category (FR2)."""
    result = pipeline.recommend(request.user_id, request.purchase_records or None)
    return result.model_dump()


@router.post("/model/train")
def train_model(request: TrainModelRequest):
    """Train GradientBoosting classifier and persist to data/models/."""
    metadata = pipeline.train(request.purchase_records or None)
    return {"status": "trained", "metadata": metadata}


@router.get("/model/info")
def model_info():
    return pipeline.model_info()
