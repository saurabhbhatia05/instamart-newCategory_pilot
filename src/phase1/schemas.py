"""Phase 1 request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.models.domain import Category, PurchaseRecord


class ScoringBreakdown(BaseModel):
    rule_score: float
    survey_boost: float
    ml_probability: float
    feedback_adjustment: float
    final_score: float


class CategoryScore(BaseModel):
    category: Category
    score: float
    reason_tags: list[str] = Field(default_factory=list)
    scoring: ScoringBreakdown | None = None


class FrequentCategory(BaseModel):
    category: Category
    purchase_count: int


class PurchaseAnalysisReport(BaseModel):
    """Output of purchase history analysis (Phase 1 Step 1)."""

    user_id: str
    is_repetitive_buyer: bool
    is_high_frequency_shopper: bool
    frequent_categories: list[FrequentCategory]
    missing_categories: list[Category]
    affinity_candidates: list[Category]
    dominant_shopping_day: str | None
    replenishment_due_categories: list[Category]
    category_diversity_index: float
    orders_per_week: float
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationResult(BaseModel):
    """Phase 1 recommendation output before explainability (Phase 2)."""

    user_id: str
    recommendation: CategoryScore | None
    analysis: PurchaseAnalysisReport
    scoring: ScoringBreakdown | None = None
    meets_confidence_threshold: bool
    latency_ms: float


class TrainModelRequest(BaseModel):
    purchase_records: list[PurchaseRecord] = Field(default_factory=list)


class AnalyzeHistoryRequest(BaseModel):
    user_id: str
    purchase_records: list[PurchaseRecord] = Field(default_factory=list)
