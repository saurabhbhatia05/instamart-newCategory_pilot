"""Shared feature vector builder for Phase 1 engine and ML trainer."""

import numpy as np

from src.phase1.purchase_history.analyzer import PurchaseHistoryAnalyzer
from src.shared.models.domain import Category, PurchaseHistory
from src.shared.survey.pdf_parser import load_survey_summary

FEATURE_NAMES = [
    "affinity_hits",
    "survey_hit",
    "diversity",
    "repetitive",
    "bias",
]


class FeatureBuilder:
    """Build ML feature vectors per architecture §6.2."""

    def __init__(self, analyzer: PurchaseHistoryAnalyzer | None = None) -> None:
        self.analyzer = analyzer or PurchaseHistoryAnalyzer()
        self.survey = load_survey_summary()

    def build(
        self, history: PurchaseHistory, candidate: Category
    ) -> np.ndarray:
        purchased = history.categories_purchased
        affinity_hits = sum(
            1
            for cat in purchased
            if candidate
            in self.analyzer.get_affinity_candidates(
                PurchaseHistory(
                    user_id=history.user_id,
                    records=[r for r in history.records if r.category == cat],
                )
            )
        )
        survey_hit = (
            1.0 if candidate.value in self.survey.top_exploration_categories else 0.0
        )
        diversity = len(purchased) / len(Category)
        repetitive = 1.0 if history.is_repetitive_buyer else 0.0

        return np.array(
            [affinity_hits, survey_hit, diversity, repetitive, 1.0], dtype=float
        )
