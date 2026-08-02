"""Build UI-ready recommendation cards from Phase 1 engine output."""

from uuid import uuid4

from src.phase1.purchase_history.analyzer import PurchaseHistoryAnalyzer
from src.phase1.recommendation_engine.engine import CategoryRecommendationEngine
from src.phase2.cards.catalog import CATEGORY_PRODUCTS, COMPETITOR_NAMES
from src.phase2.explainability.layer import ExplainabilityLayer
from src.phase2.schemas import RecommendationCard, SmartReward
from src.shared.models.domain import PurchaseHistory


class RecommendationCardBuilder:
    """Phase 2: Assemble recommendation card with products, bundles, rewards."""

    def __init__(
        self,
        engine: CategoryRecommendationEngine | None = None,
        explainer: ExplainabilityLayer | None = None,
    ) -> None:
        self.engine = engine or CategoryRecommendationEngine()
        self.explainer = explainer or ExplainabilityLayer()
        self.analyzer = PurchaseHistoryAnalyzer()

    def build(self, history: PurchaseHistory) -> RecommendationCard | None:
        scored = self.engine.recommend_one(history)
        if not scored:
            return None

        explanation = self.explainer.generate(
            history, scored.category, scored.reason_tags
        )
        products = CATEGORY_PRODUCTS.get(scored.category, [])
        freq_cat = self.analyzer.get_frequent_categories(history, top_n=1)
        bundle_source = freq_cat[0][0] if freq_cat else scored.category
        bundles = self.explainer.bundle_suggestion(bundle_source)

        rewards = [
            SmartReward(
                label="First purchase bonus",
                value="50 Instamart Coins",
                type="coins",
            ),
            SmartReward(label="Bundle discount", value="5% off", type="cashback"),
        ]

        price_note = self._price_comparison_note(products)

        return RecommendationCard(
            recommendation_id=str(uuid4()),
            user_id=history.user_id,
            category=scored.category,
            headline=explanation.headline,
            reason=explanation.reason,
            trust_signal=explanation.trust_signal,
            context=explanation.context,
            products=products,
            bundle_items=bundles,
            rewards=rewards,
            price_comparison_note=price_note,
            confidence_score=round(scored.score, 3),
            explainability_source=explanation.source,
        )

    def _price_comparison_note(self, products) -> str | None:
        if not products or not products[0].competitor_price_inr:
            return None
        savings = products[0].competitor_price_inr - products[0].price_inr
        if savings <= 0:
            return None
        return f"₹{savings:.0f} cheaper than {COMPETITOR_NAMES[0]}"
