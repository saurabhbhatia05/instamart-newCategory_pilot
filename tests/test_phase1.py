"""Phase 1 unit tests."""

from datetime import datetime, timedelta

import pytest

from data.sample.purchase_history import sample_history
from src.phase1.pipeline import DiscoveryPipeline
from src.phase1.purchase_history.analyzer import PurchaseHistoryAnalyzer
from src.phase1.recommendation_engine.engine import CategoryRecommendationEngine
from src.shared.models.domain import Category, PurchaseHistory, PurchaseRecord


@pytest.fixture
def pipeline() -> DiscoveryPipeline:
    return DiscoveryPipeline()


@pytest.fixture
def repetitive_history() -> PurchaseHistory:
    return sample_history("test_user")


def test_fr1_repetitive_buyer_detection(repetitive_history: PurchaseHistory):
    assert repetitive_history.is_repetitive_buyer is True


def test_analyzer_missing_categories(repetitive_history: PurchaseHistory):
    analyzer = PurchaseHistoryAnalyzer()
    missing = analyzer.get_missing_categories(repetitive_history)
    assert Category.HEALTH_WELLNESS in missing
    assert Category.MILK not in missing


def test_analyzer_full_report(repetitive_history: PurchaseHistory):
    report = PurchaseHistoryAnalyzer().analyze(repetitive_history)
    assert report.user_id == "test_user"
    assert report.is_repetitive_buyer is True
    assert len(report.frequent_categories) >= 1
    assert len(report.missing_categories) >= 1


def test_fr2_exactly_one_recommendation(repetitive_history: PurchaseHistory):
    engine = CategoryRecommendationEngine()
    result = engine.recommend_one(repetitive_history)
    assert result is not None
    assert isinstance(result.category, Category)
    assert result.score >= 0.65


def test_pipeline_recommend(pipeline: DiscoveryPipeline):
    result = pipeline.recommend("user_001")
    assert result.meets_confidence_threshold is True
    assert result.recommendation is not None
    assert result.latency_ms < 500
    assert result.scoring is not None


def test_model_train_and_predict(pipeline: DiscoveryPipeline):
    meta = pipeline.train()
    assert meta["n_samples"] > 0
    info = pipeline.model_info()
    assert info["trained"] is True


def test_non_repetitive_user_gets_no_recommendation():
    history = PurchaseHistory(
        user_id="sparse_user",
        records=[
            PurchaseRecord(
                user_id="sparse_user",
                product_id="p1",
                product_name="Milk",
                category=Category.MILK,
                quantity=1,
                price_inr=50.0,
                purchased_at=datetime.utcnow(),
            )
        ],
    )
    assert CategoryRecommendationEngine().recommend_one(history) is None
