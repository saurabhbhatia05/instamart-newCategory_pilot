"""Phase 1 orchestration: analyze → score → recommend."""

import time

from data.sample.purchase_history import sample_history
from src.phase1.models.trainer import CategoryModelTrainer
from src.phase1.purchase_history.analyzer import PurchaseHistoryAnalyzer
from src.phase1.recommendation_engine.engine import CategoryRecommendationEngine
from src.phase1.schemas import RecommendationResult
from src.shared.models.domain import PurchaseHistory, PurchaseRecord


class DiscoveryPipeline:
    """
    Phase 1 entry point implementing architecture §6 workflow:
    analyze purchase history → identify gaps → predict category → return one rec.
    """

    def __init__(
        self,
        analyzer: PurchaseHistoryAnalyzer | None = None,
        engine: CategoryRecommendationEngine | None = None,
        trainer: CategoryModelTrainer | None = None,
    ) -> None:
        self.analyzer = analyzer or PurchaseHistoryAnalyzer()
        self.trainer = trainer or CategoryModelTrainer()
        self.engine = engine or CategoryRecommendationEngine(
            analyzer=self.analyzer, trainer=self.trainer
        )

    def _resolve_history(
        self, user_id: str, records: list[PurchaseRecord] | None = None
    ) -> PurchaseHistory:
        if records:
            return PurchaseHistory(user_id=user_id, records=records)
        return sample_history(user_id)

    def analyze(
        self, user_id: str, records: list[PurchaseRecord] | None = None
    ):
        history = self._resolve_history(user_id, records)
        return self.analyzer.analyze(history)

    def recommend(
        self, user_id: str, records: list[PurchaseRecord] | None = None
    ) -> RecommendationResult:
        start = time.perf_counter()
        history = self._resolve_history(user_id, records)
        analysis = self.analyzer.analyze(history)
        recommendation = self.engine.recommend_one(history)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return RecommendationResult(
            user_id=user_id,
            recommendation=recommendation,
            analysis=analysis,
            scoring=recommendation.scoring if recommendation else None,
            meets_confidence_threshold=recommendation is not None,
            latency_ms=round(elapsed_ms, 2),
        )

    def train(self, records: list[PurchaseRecord] | None = None) -> dict:
        return self.trainer.train(records)

    def model_info(self) -> dict:
        return self.trainer.model_info()
