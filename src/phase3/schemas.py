"""Phase 3 request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    user_id: str
    recommendation_id: str
    rating: int = Field(ge=1, le=5)
    added_to_cart: bool = False
    purchased: bool = False
    comment: str | None = None
    variant: str | None = None


class ABAssignmentResponse(BaseModel):
    user_id: str
    variant: str
    experiment_enabled: bool
    control_ratio: float


class ExperimentResults(BaseModel):
    variants: dict
    lift_pct: float
    target_kpi_lift: str
    statistical_note: str | None = None


class FeedbackSummary(BaseModel):
    total: int
    avg_rating: float
    purchase_rate: float
    cart_add_rate: float


class DashboardResponse(BaseModel):
    kpis: dict
    counts: dict
    north_star: dict
    secondary_kpis: list[str]
    ab_test: dict
    feedback: FeedbackSummary
    generated_at: datetime = Field(default_factory=datetime.utcnow)
