"""Analyze purchase history to identify patterns and missing categories."""

from collections import Counter
from datetime import datetime, timedelta

from src.phase1.schemas import FrequentCategory, PurchaseAnalysisReport
from src.shared.models.domain import Category, PurchaseHistory, PurchaseRecord


# Categories users most want to explore (from survey + PRD)
EXPLORATION_PRIORITY: list[Category] = [
    Category.HEALTH_WELLNESS,
    Category.PET_SUPPLIES,
    Category.HOUSEHOLD,
    Category.PERSONAL_CARE,
    Category.BABY_CARE,
    Category.SNACKS,
    Category.FROZEN,
]

# Category affinity: if user buys X, likely to need Y
CATEGORY_AFFINITY: dict[Category, list[Category]] = {
    Category.MILK: [Category.BREAD, Category.SNACKS, Category.HEALTH_WELLNESS],
    Category.BREAD: [Category.MILK, Category.SNACKS, Category.HOUSEHOLD],
    Category.FRUITS: [Category.HEALTH_WELLNESS, Category.SNACKS, Category.FROZEN],
    Category.BABY_CARE: [Category.HOUSEHOLD, Category.PERSONAL_CARE, Category.HEALTH_WELLNESS],
    Category.SNACKS: [Category.SNACKS, Category.HOUSEHOLD, Category.PERSONAL_CARE],
}


class PurchaseHistoryAnalyzer:
    """Phase 1: Analyze purchase history for cross-category opportunities."""

    def get_frequent_categories(
        self, history: PurchaseHistory, top_n: int = 3
    ) -> list[tuple[Category, int]]:
        counts = Counter(r.category for r in history.records)
        return counts.most_common(top_n)

    def get_missing_categories(self, history: PurchaseHistory) -> list[Category]:
        purchased = history.categories_purchased
        missing: list[Category] = []
        for cat in EXPLORATION_PRIORITY:
            if cat not in purchased:
                missing.append(cat)
        return missing

    def get_affinity_candidates(self, history: PurchaseHistory) -> list[Category]:
        """Categories related to user's existing purchases."""
        candidates: list[Category] = []
        purchased = history.categories_purchased
        for cat in purchased:
            for related in CATEGORY_AFFINITY.get(cat, []):
                if related not in purchased and related not in candidates:
                    candidates.append(related)
        return candidates

    def get_purchase_frequency(
        self, history: PurchaseHistory, category: Category
    ) -> dict:
        cat_records = [r for r in history.records if r.category == category]
        if not cat_records:
            return {"count": 0, "avg_days_between": None, "day_of_week": None}

        cat_records.sort(key=lambda r: r.purchased_at)
        intervals = [
            (cat_records[i].purchased_at - cat_records[i - 1].purchased_at).days
            for i in range(1, len(cat_records))
        ]
        days = [r.purchased_at.strftime("%A") for r in cat_records]
        day_counts = Counter(days)

        return {
            "count": len(cat_records),
            "avg_days_between": sum(intervals) / len(intervals) if intervals else None,
            "day_of_week": day_counts.most_common(1)[0][0] if day_counts else None,
        }

    def detect_replenishment_due(
        self, history: PurchaseHistory, category: Category, threshold_days: int = 7
    ) -> bool:
        cat_records = [r for r in history.records if r.category == category]
        if not cat_records:
            return False
        last = max(cat_records, key=lambda r: r.purchased_at)
        freq = self.get_purchase_frequency(history, category)
        avg_days = freq.get("avg_days_between")
        if avg_days is None:
            return False
        days_since = (datetime.utcnow() - last.purchased_at).days
        return days_since >= avg_days - threshold_days

    def get_dominant_day(self, history: PurchaseHistory) -> str | None:
        if not history.records:
            return None
        days = [r.purchased_at.strftime("%A") for r in history.records]
        return Counter(days).most_common(1)[0][0]

    def get_category_diversity_index(self, history: PurchaseHistory) -> float:
        if not history.records:
            return 0.0
        return len(history.categories_purchased) / len(Category)

    def get_orders_per_week(self, history: PurchaseHistory) -> float:
        if len(history.records) < 2:
            return 0.0
        dates = sorted(r.purchased_at for r in history.records)
        span_days = max((dates[-1] - dates[0]).days, 1)
        unique_order_days = len({d.date() for d in dates})
        return round(unique_order_days / (span_days / 7), 2)

    def is_high_frequency_shopper(self, history: PurchaseHistory) -> bool:
        """Target segment: 3–5 shops/week (PRD §3)."""
        return self.get_orders_per_week(history) >= 3.0

    def get_replenishment_due_categories(
        self, history: PurchaseHistory
    ) -> list[Category]:
        due: list[Category] = []
        for cat in history.categories_purchased:
            if self.detect_replenishment_due(history, cat):
                due.append(cat)
        return due

    def analyze(self, history: PurchaseHistory) -> PurchaseAnalysisReport:
        """Full purchase history analysis report for Phase 1 pipeline."""
        return PurchaseAnalysisReport(
            user_id=history.user_id,
            is_repetitive_buyer=history.is_repetitive_buyer,
            is_high_frequency_shopper=self.is_high_frequency_shopper(history),
            frequent_categories=[
                FrequentCategory(category=cat, purchase_count=count)
                for cat, count in self.get_frequent_categories(history)
            ],
            missing_categories=self.get_missing_categories(history),
            affinity_candidates=self.get_affinity_candidates(history),
            dominant_shopping_day=self.get_dominant_day(history),
            replenishment_due_categories=self.get_replenishment_due_categories(history),
            category_diversity_index=round(
                self.get_category_diversity_index(history), 3
            ),
            orders_per_week=self.get_orders_per_week(history),
        )
