"""Phase 2 unit tests."""

from src.phase2.cards.builder import RecommendationCardBuilder
from src.phase2.explainability.layer import ExplainabilityLayer
from src.phase2.service import DiscoveryUIService
from data.sample.purchase_history import sample_history


def test_card_builder_returns_card():
    history = sample_history("user_001")
    builder = RecommendationCardBuilder()
    card = builder.build(history)
    assert card is not None
    assert card.headline
    assert card.reason
    assert card.trust_signal
    assert card.confidence_score >= 0.65
    assert card.explainability_source in ("rules", "grok")


def test_explainability_rule_fallback():
    history = sample_history("user_001")
    explainer = ExplainabilityLayer()
    from src.phase1.recommendation_engine.engine import CategoryRecommendationEngine

    scored = CategoryRecommendationEngine().recommend_one(history)
    assert scored is not None
    explanation = explainer.generate(history, scored.category, scored.reason_tags)
    assert explanation.headline
    assert explanation.reason
    assert explanation.source in ("rules", "grok")


def test_ui_service_card_response():
    service = DiscoveryUIService()
    response = service.get_card_response("user_001")
    assert response.variant == "treatment"
    assert response.latency_ms < 500
    assert response.recommendation is not None
    assert len(response.recommendation.products) >= 1
