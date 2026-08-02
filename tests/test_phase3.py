"""Phase 3 unit tests."""

from src.shared.models.domain import Category
from src.app.dependencies import experiment_service
from src.phase3.schemas import FeedbackRequest


def test_ab_assignment_is_deterministic():
    a = experiment_service.assign_variant("user_abc")
    b = experiment_service.assign_variant("user_abc")
    assert a.variant == b.variant
    assert a.variant in ("control", "treatment")


def test_feedback_updates_analytics_and_ab():
    assignment = experiment_service.assign_variant("feedback_user")
    experiment_service.register_impression(
        "feedback_user",
        "rec_test_001",
        Category.HEALTH_WELLNESS,
        assignment.variant,
    )

    result = experiment_service.process_feedback(
        FeedbackRequest(
            user_id="feedback_user",
            recommendation_id="rec_test_001",
            rating=5,
            added_to_cart=True,
            purchased=True,
            variant=assignment.variant,
        )
    )
    assert result["status"] == "recorded"
    assert result["model_updated"] is True

    dashboard = experiment_service.get_dashboard()
    assert dashboard.counts["impressions"] >= 1
    assert dashboard.counts["purchases"] >= 1
    assert dashboard.feedback.total >= 1


def test_ab_results_structure():
    results = experiment_service.get_ab_results()
    assert "variants" in results
    assert "control" in results["variants"]
    assert "treatment" in results["variants"]
    assert "lift_pct" in results
