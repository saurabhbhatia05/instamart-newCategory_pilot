"""Phase 2 service — orchestrates Phase 1 pipeline with cards and explainability."""

import time

from config.settings import settings
from data.sample.purchase_history import sample_history
from src.phase1.pipeline import DiscoveryPipeline
from src.phase2.cards.builder import RecommendationCardBuilder
from src.phase2.schemas import CardResponse, RecommendationCard
from src.shared.models.domain import PurchaseHistory, PurchaseRecord


class DiscoveryUIService:
    """
    Phase 2 entry point: purchase history → recommendation card for UI.
    Implements architecture §6 workflow steps through explainability + card assembly.
    """

    def __init__(self, pipeline: DiscoveryPipeline | None = None) -> None:
        self.pipeline = pipeline or DiscoveryPipeline()
        self.card_builder = RecommendationCardBuilder(engine=self.pipeline.engine)

    def _resolve_history(
        self, user_id: str, records: list[PurchaseRecord] | None = None
    ) -> PurchaseHistory:
        if records:
            return PurchaseHistory(user_id=user_id, records=records)
        return sample_history(user_id)

    def build_card(
        self, user_id: str, records: list[PurchaseRecord] | None = None
    ) -> tuple[RecommendationCard | None, float]:
        start = time.perf_counter()
        history = self._resolve_history(user_id, records)
        card = self.card_builder.build(history)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return card, round(elapsed_ms, 2)

    def get_card_response(
        self,
        user_id: str,
        records: list[PurchaseRecord] | None = None,
        variant: str = "treatment",
    ) -> CardResponse:
        card, latency_ms = self.build_card(user_id, records)

        if not card:
            return CardResponse(
                variant=variant,
                recommendation=None,
                message="No high-confidence recommendation for this user",
                latency_ms=latency_ms,
                llm_enabled=settings.llm_enabled,
            )

        return CardResponse(
            variant=variant,
            recommendation=card,
            latency_ms=latency_ms,
            llm_enabled=settings.llm_enabled,
        )
