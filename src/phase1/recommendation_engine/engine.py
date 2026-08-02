"""Collaborative filtering + rule-based + ML category recommendation engine."""

import numpy as np

from config.settings import settings
from src.phase1.features import FeatureBuilder
from src.phase1.models.trainer import CategoryModelTrainer
from src.phase1.purchase_history.analyzer import EXPLORATION_PRIORITY, PurchaseHistoryAnalyzer
from src.phase1.schemas import CategoryScore, ScoringBreakdown
from src.shared.models.domain import Category, PurchaseHistory
from src.shared.survey.pdf_parser import load_survey_summary

RULE_WEIGHT = 0.30
ML_WEIGHT = 0.50
SURVEY_WEIGHT = 0.20
ML_FEATURE_WEIGHTS = np.array([0.25, 0.30, 0.15, 0.20, 0.10])


class CategoryRecommendationEngine:
    """
    Phase 1: Recommend exactly one new category (FR2).
    Combines rule-based affinity, survey insights, and ML scoring.
    """

    def __init__(
        self,
        analyzer: PurchaseHistoryAnalyzer | None = None,
        trainer: CategoryModelTrainer | None = None,
    ) -> None:
        self.analyzer = analyzer or PurchaseHistoryAnalyzer()
        self.trainer = trainer or CategoryModelTrainer()
        self.feature_builder = FeatureBuilder(self.analyzer)
        self.survey = load_survey_summary()
        self._feedback_weights: dict[str, float] = {}

    def _survey_boost(self, category: Category) -> float:
        cat_name = category.value
        if cat_name in self.survey.top_exploration_categories:
            idx = self.survey.top_exploration_categories.index(cat_name)
            return 0.15 * (1 - idx * 0.1)
        return 0.0

    def _exploration_priority_boost(self, category: Category) -> float:
        if category not in EXPLORATION_PRIORITY:
            return 0.0
        idx = EXPLORATION_PRIORITY.index(category)
        return 0.12 * (1 - idx * 0.12)

    def _rule_score(
        self, history: PurchaseHistory, candidate: Category
    ) -> tuple[float, list[str]]:
        tags: list[str] = []
        score = 0.0
        affinity = self.analyzer.get_affinity_candidates(history)
        if candidate in affinity:
            score += 0.35
            tags.append("related_to_purchase_history")

        freq_cats = self.analyzer.get_frequent_categories(history)
        for cat, count in freq_cats:
            related = self.analyzer.get_affinity_candidates(
                PurchaseHistory(
                    user_id=history.user_id,
                    records=[r for r in history.records if r.category == cat],
                )
            )
            if candidate in related:
                score += 0.1 * min(count / len(history.records), 0.5)
                tags.append(f"because_you_buy_{cat.value.lower().replace(' ', '_')}")

        return min(score, 1.0), tags

    def _ml_score(self, features: np.ndarray, candidate: Category) -> float:
        """Blend feature-vector scoring with trained classifier probability."""
        dot_score = float(np.dot(features, ML_FEATURE_WEIGHTS))
        dot_score = min(max(dot_score, 0.0), 1.0)
        if self.trainer.is_trained:
            model_prob = self.trainer.category_probability(features, candidate)
            return 0.5 * dot_score + 0.5 * model_prob
        return dot_score

    def _combine_scores(
        self,
        rule_score: float,
        survey_boost: float,
        ml_probability: float,
        feedback_adjustment: float,
        exploration_boost: float = 0.0,
    ) -> ScoringBreakdown:
        base = (
            RULE_WEIGHT * rule_score
            + SURVEY_WEIGHT * min(survey_boost * 5, 1.0)
            + ML_WEIGHT * ml_probability
            + exploration_boost
        )
        final = base + feedback_adjustment
        return ScoringBreakdown(
            rule_score=round(rule_score, 4),
            survey_boost=round(survey_boost, 4),
            ml_probability=round(ml_probability, 4),
            feedback_adjustment=round(feedback_adjustment, 4),
            final_score=round(final, 4),
        )

    def score_candidates(self, history: PurchaseHistory) -> list[CategoryScore]:
        missing = self.analyzer.get_missing_categories(history)
        if not missing:
            return []

        scored: list[CategoryScore] = []
        for candidate in missing:
            rule_score, tags = self._rule_score(history, candidate)
            survey_boost = self._survey_boost(candidate)
            features = self.feature_builder.build(history, candidate)
            ml_probability = self._ml_score(features, candidate)

            feedback_key = f"{history.user_id}:{candidate.value}"
            feedback_adjustment = self._feedback_weights.get(feedback_key, 0.0)
            exploration_boost = self._exploration_priority_boost(candidate)
            breakdown = self._combine_scores(
                rule_score,
                survey_boost,
                ml_probability,
                feedback_adjustment,
                exploration_boost,
            )

            scored.append(
                CategoryScore(
                    category=candidate,
                    score=breakdown.final_score,
                    reason_tags=tags,
                    scoring=breakdown,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def recommend_one(self, history: PurchaseHistory) -> CategoryScore | None:
        """FR2: Return exactly one category above confidence threshold."""
        if not history.is_repetitive_buyer:
            return None

        candidates = self.score_candidates(history)
        if not candidates:
            return None

        best = candidates[0]
        if best.score < settings.recommendation_confidence_threshold:
            return None
        return best

    def update_from_feedback(
        self, user_id: str, category: Category, rating: int, purchased: bool
    ) -> None:
        """FR5: Adjust weights based on user feedback."""
        key = f"{user_id}:{category.value}"
        delta = (rating - 3) * 0.05
        if purchased:
            delta += 0.1
        self._feedback_weights[key] = self._feedback_weights.get(key, 0.0) + delta
