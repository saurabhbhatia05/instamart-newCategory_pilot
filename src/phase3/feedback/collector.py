"""Collect and apply user feedback to improve recommendations (FR5)."""

from src.phase1.recommendation_engine.engine import CategoryRecommendationEngine
from src.shared.models.domain import Category, PurchaseRecord, RecommendationFeedback


class FeedbackCollector:
    """Phase 3: Feedback loop for continuous improvement."""

    def __init__(self, engine: CategoryRecommendationEngine) -> None:
        self.engine = engine
        self._history: list[RecommendationFeedback] = []
        self._category_map: dict[str, Category] = {}
        self._variant_map: dict[str, str] = {}

    def register_recommendation(
        self,
        recommendation_id: str,
        category: Category,
        user_id: str,
        variant: str = "treatment",
    ) -> None:
        self._category_map[recommendation_id] = category
        self._variant_map[recommendation_id] = variant

    def collect(self, feedback: RecommendationFeedback) -> dict:
        self._history.append(feedback)
        category = self._category_map.get(feedback.recommendation_id)
        variant = self._variant_map.get(feedback.recommendation_id, "treatment")

        if category:
            self.engine.update_from_feedback(
                feedback.user_id,
                category,
                feedback.rating,
                feedback.purchased,
            )

        return {
            "recorded": True,
            "variant": variant,
            "model_updated": category is not None,
            "recommendation_id": feedback.recommendation_id,
        }

    def get_training_records(self) -> list[PurchaseRecord]:
        """Export synthetic purchase records from feedback for batch retraining."""
        records: list[PurchaseRecord] = []
        for fb in self._history:
            if not fb.purchased:
                continue
            cat = self._category_map.get(fb.recommendation_id)
            if not cat:
                continue
            records.append(
                PurchaseRecord(
                    user_id=fb.user_id,
                    product_id=f"fb_{fb.recommendation_id[:8]}",
                    product_name=f"Cross-category {cat.value}",
                    category=cat,
                    quantity=1,
                    price_inr=199.0,
                    purchased_at=fb.created_at,
                )
            )
        return records

    def get_summary(self) -> dict:
        if not self._history:
            return {
                "total": 0,
                "avg_rating": 0.0,
                "purchase_rate": 0.0,
                "cart_add_rate": 0.0,
            }
        total = len(self._history)
        return {
            "total": total,
            "avg_rating": round(sum(f.rating for f in self._history) / total, 2),
            "purchase_rate": round(
                sum(1 for f in self._history if f.purchased) / total, 4
            ),
            "cart_add_rate": round(
                sum(1 for f in self._history if f.added_to_cart) / total, 4
            ),
        }
