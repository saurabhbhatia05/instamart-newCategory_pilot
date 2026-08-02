"""Shared domain models across all phases."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    MILK = "Milk & Dairy"
    BREAD = "Bread & Bakery"
    FRUITS = "Fruits & Vegetables"
    PET_SUPPLIES = "Pet Supplies"
    HEALTH_WELLNESS = "Health & Wellness"
    PERSONAL_CARE = "Beauty & Personal Care"
    HOUSEHOLD = "Household Essentials"
    SNACKS = "Snacks & Beverages"
    BABY_CARE = "Baby Care"
    FROZEN = "Frozen Foods"


class PurchaseRecord(BaseModel):
    user_id: str
    product_id: str
    product_name: str
    category: Category
    quantity: int = 1
    price_inr: float
    purchased_at: datetime


class PurchaseHistory(BaseModel):
    user_id: str
    records: list[PurchaseRecord] = Field(default_factory=list)

    @property
    def categories_purchased(self) -> set[Category]:
        return {r.category for r in self.records}

    @property
    def is_repetitive_buyer(self) -> bool:
        """FR1: Identify users with repetitive buying behaviour."""
        if len(self.records) < 3:
            return False
        category_counts: dict[Category, int] = {}
        for r in self.records:
            category_counts[r.category] = category_counts.get(r.category, 0) + 1
        top_count = max(category_counts.values()) if category_counts else 0
        return top_count / len(self.records) >= 0.6


class SurveyInsight(BaseModel):
    finding: str
    frequency: int
    percentage: float


class SurveySummary(BaseModel):
    total_respondents: int
    insights: list[SurveyInsight]
    top_exploration_categories: list[str]
    top_barriers: list[str]
    willingness_score: float  # 0-1 scale


class RecommendationFeedback(BaseModel):
    user_id: str
    recommendation_id: str
    rating: int = Field(ge=1, le=5)
    added_to_cart: bool = False
    purchased: bool = False
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KPIRecord(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cross_category_purchase_rate: float
    category_adoption_rate: float
    recommendation_ctr: float
    recommendation_conversion: float
    average_order_value: float
    basket_size: float
    category_diversity_index: float
    monthly_active_new_category_pct: float
