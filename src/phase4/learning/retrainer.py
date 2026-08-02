"""Continuous learning from feedback — Phase 4."""

from config.settings import settings
from src.phase1.pipeline import DiscoveryPipeline
from src.phase3.analytics.dashboard import AnalyticsDashboard
from src.phase3.feedback.collector import FeedbackCollector


class ContinuousLearner:
    """
    Phase 4: Batch retrain when ENABLE_CONTINUOUS_LEARNING=true.
    Validates KPI lift before promoting new model weights.
    """

    MIN_FEEDBACK_FOR_RETRAIN = 5

    def __init__(
        self,
        pipeline: DiscoveryPipeline,
        feedback_collector: FeedbackCollector,
        analytics: AnalyticsDashboard,
    ) -> None:
        self.pipeline = pipeline
        self.feedback = feedback_collector
        self.analytics = analytics
        self._last_retrain_at: str | None = None
        self._retrain_count = 0

    def should_retrain(self) -> bool:
        if not settings.enable_continuous_learning:
            return False
        summary = self.feedback.get_summary()
        return summary["total"] >= self.MIN_FEEDBACK_FOR_RETRAIN

    def retrain(self, force: bool = False) -> dict:
        if not force and not self.should_retrain():
            return {
                "status": "skipped",
                "reason": "Continuous learning disabled or insufficient feedback",
                "min_feedback_required": self.MIN_FEEDBACK_FOR_RETRAIN,
                "current_feedback": self.feedback.get_summary()["total"],
            }

        kpi_before = self.analytics.get_kpi_summary()["kpis"]
        records = self.feedback.get_training_records()
        metadata = self.pipeline.train(records or None)

        from datetime import datetime

        self._last_retrain_at = datetime.utcnow().isoformat()
        self._retrain_count += 1

        kpi_after = self.analytics.get_kpi_summary()["kpis"]
        promoted = kpi_after.get("recommendation_conversion", 0) >= kpi_before.get(
            "recommendation_conversion", 0
        )

        return {
            "status": "trained",
            "triggered_by": "continuous_learning" if not force else "manual",
            "metadata": metadata,
            "kpi_before": kpi_before,
            "kpi_after": kpi_after,
            "promoted": promoted,
            "retrain_count": self._retrain_count,
            "last_retrain_at": self._last_retrain_at,
        }

    def get_status(self) -> dict:
        return {
            "enabled": settings.enable_continuous_learning,
            "should_retrain": self.should_retrain(),
            "retrain_count": self._retrain_count,
            "last_retrain_at": self._last_retrain_at,
            "feedback_summary": self.feedback.get_summary(),
        }
