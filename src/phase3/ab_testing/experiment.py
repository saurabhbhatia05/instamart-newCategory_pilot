"""A/B testing for Smart Discovery vs control widget."""

import hashlib
from dataclasses import dataclass, field

from config.settings import settings


@dataclass
class VariantStats:
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    cart_adds: int = 0

    @property
    def ctr(self) -> float:
        return self.clicks / self.impressions if self.impressions else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions else 0.0


class ABTestManager:
    """Phase 3: Split users between AI recommendation and generic control."""

    def __init__(self) -> None:
        self._stats: dict[str, VariantStats] = {
            "control": VariantStats(),
            "treatment": VariantStats(),
        }
        self._user_variants: dict[str, str] = {}

    def _compute_variant(self, user_id: str) -> str:
        if not settings.ab_test_enabled:
            return "treatment"
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = (hash_val % 100) / 100.0
        return "control" if bucket < settings.ab_test_control_ratio else "treatment"

    def assign_variant(self, user_id: str, track_impression: bool = True) -> str:
        if user_id not in self._user_variants:
            self._user_variants[user_id] = self._compute_variant(user_id)

        variant = self._user_variants[user_id]
        if track_impression:
            self._stats[variant].impressions += 1
        return variant

    def get_user_variant(self, user_id: str) -> str:
        if user_id not in self._user_variants:
            self._user_variants[user_id] = self._compute_variant(user_id)
        return self._user_variants[user_id]

    def record_click(self, variant: str) -> None:
        if variant in self._stats:
            self._stats[variant].clicks += 1

    def record_cart_add(self, variant: str) -> None:
        if variant in self._stats:
            self._stats[variant].cart_adds += 1
            self._stats[variant].clicks += 1

    def record_conversion(self, variant: str) -> None:
        if variant in self._stats:
            self._stats[variant].conversions += 1

    def get_results(self) -> dict:
        results = {}
        for variant, stats in self._stats.items():
            results[variant] = {
                "impressions": stats.impressions,
                "clicks": stats.clicks,
                "cart_adds": stats.cart_adds,
                "conversions": stats.conversions,
                "ctr": round(stats.ctr * 100, 2),
                "conversion_rate": round(stats.conversion_rate * 100, 2),
            }

        treatment_rate = results["treatment"]["conversion_rate"]
        control_rate = results["control"]["conversion_rate"]
        lift = (
            round((treatment_rate - control_rate) / control_rate * 100, 2)
            if control_rate
            else 0.0
        )

        note = None
        total_imp = sum(r["impressions"] for r in results.values())
        if total_imp < 100:
            note = "Insufficient sample size for statistical significance (<100 impressions)"

        return {
            "variants": results,
            "lift_pct": lift,
            "target_kpi_lift": "+15% cross-category purchase rate",
            "experiment_enabled": settings.ab_test_enabled,
            "control_ratio": settings.ab_test_control_ratio,
            "statistical_note": note,
        }
