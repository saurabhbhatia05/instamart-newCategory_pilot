"""Phase 3 orchestration — A/B testing, analytics, feedback loop."""

from src.phase3.ab_testing.experiment import ABTestManager
from src.phase3.analytics.dashboard import AnalyticsDashboard
from src.phase3.feedback.collector import FeedbackCollector
from src.phase3.schemas import (
    ABAssignmentResponse,
    DashboardResponse,
    FeedbackRequest,
    FeedbackSummary,
)
from src.shared.models.domain import Category, RecommendationFeedback


class ExperimentService:
    """
    Phase 3 entry point: experiment assignment, event tracking, dashboard, feedback.
    """

    def __init__(
        self,
        ab_manager: ABTestManager,
        analytics: AnalyticsDashboard,
        feedback_collector: FeedbackCollector,
    ) -> None:
        self.ab = ab_manager
        self.analytics = analytics
        self.feedback = feedback_collector

    def assign_variant(self, user_id: str) -> ABAssignmentResponse:
        variant = self.ab.assign_variant(user_id)
        from config.settings import settings

        return ABAssignmentResponse(
            user_id=user_id,
            variant=variant,
            experiment_enabled=settings.ab_test_enabled,
            control_ratio=settings.ab_test_control_ratio,
        )

    def register_impression(
        self,
        user_id: str,
        recommendation_id: str,
        category: Category,
        variant: str = "treatment",
    ) -> None:
        self.feedback.register_recommendation(
            recommendation_id, category, user_id, variant
        )
        self.analytics.track_impression(
            user_id, recommendation_id, category, variant
        )

    def process_feedback(self, request: FeedbackRequest) -> dict:
        feedback = RecommendationFeedback(
            user_id=request.user_id,
            recommendation_id=request.recommendation_id,
            rating=request.rating,
            added_to_cart=request.added_to_cart,
            purchased=request.purchased,
            comment=request.comment,
        )

        result = self.feedback.collect(feedback)
        self.analytics.track_feedback(feedback)

        variant = request.variant or result.get("variant", "treatment")
        if request.added_to_cart:
            self.ab.record_cart_add(variant)
        elif request.rating >= 4:
            self.ab.record_click(variant)

        if request.purchased:
            self.ab.record_conversion(variant)

        return {
            "status": "recorded",
            "message": "Feedback will improve future recommendations",
            **result,
        }

    def get_dashboard(self) -> DashboardResponse:
        kpi_data = self.analytics.get_kpi_summary()
        fb_summary = self.feedback.get_summary()
        return DashboardResponse(
            kpis=kpi_data["kpis"],
            counts=kpi_data["counts"],
            north_star=kpi_data["north_star"],
            secondary_kpis=kpi_data["secondary_kpis"],
            ab_test=self.ab.get_results(),
            feedback=FeedbackSummary(**fb_summary),
        )

    def get_ab_results(self) -> dict:
        return self.ab.get_results()
