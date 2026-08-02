"""Phase 2 REST API — recommendation cards, UI integration."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.app.dependencies import ui_service
from src.phase2.schemas import CardRequest, CardResponse

router = APIRouter(prefix="/api/v1/phase2", tags=["Phase 2 — UI Integration"])

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@router.get("/health")
def phase2_health():
    return {
        "phase": 2,
        "status": "ready",
        "llm_enabled": settings.llm_enabled,
        "llm_provider": settings.llm_provider if settings.llm_enabled else None,
        "components": [
            "service.py",
            "cards/builder.py",
            "explainability/layer.py",
            "explainability/grok_client.py",
            "frontend/",
        ],
    }


@router.post("/cards", response_model=CardResponse)
def build_recommendation_card(request: CardRequest):
    """Build a full recommendation card with explainability (FR3)."""
    return ui_service.get_card_response(
        request.user_id,
        request.purchase_records or None,
    )


@router.post("/cards/demo", response_model=CardResponse)
def demo_card():
    """Demo card for user_001 using sample purchase history."""
    return ui_service.get_card_response("user_001")


def mount_frontend(app) -> None:
    """Mount Phase 2 static frontend and home route on the FastAPI app."""

    @app.get("/")
    def serve_home():
        return FileResponse(FRONTEND_DIR / "index.html")

    if FRONTEND_DIR.exists():
        app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
