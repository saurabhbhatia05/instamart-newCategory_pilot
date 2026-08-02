"""Phase 2 API schemas — recommendation cards and UI responses."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.models.domain import Category, PurchaseRecord


class ProductItem(BaseModel):
    product_id: str
    name: str
    price_inr: float
    mrp_inr: float
    rating: float = 4.5
    discount_pct: float | None = None
    competitor_price_inr: float | None = None


class SmartReward(BaseModel):
    label: str
    value: str
    type: str


class RecommendationCard(BaseModel):
    recommendation_id: str
    user_id: str
    category: Category
    headline: str
    reason: str
    trust_signal: str
    context: str
    products: list[ProductItem]
    bundle_items: list[str] = Field(default_factory=list)
    rewards: list[SmartReward] = Field(default_factory=list)
    price_comparison_note: str | None = None
    confidence_score: float
    explainability_source: str = "rules"
    one_click_add_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CardRequest(BaseModel):
    user_id: str
    purchase_records: list[PurchaseRecord] = Field(default_factory=list)


class CardResponse(BaseModel):
    variant: str = "treatment"
    recommendation: RecommendationCard | None = None
    message: str | None = None
    latency_ms: float
    llm_enabled: bool = False
