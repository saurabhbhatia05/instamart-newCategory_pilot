"""Generate human-readable explanations for recommendations (FR3)."""

from dataclasses import dataclass

from src.phase1.purchase_history.analyzer import PurchaseHistoryAnalyzer
from src.phase2.explainability.grok_client import GrokLLMClient
from src.shared.models.domain import Category, PurchaseHistory


@dataclass
class Explanation:
    headline: str
    reason: str
    trust_signal: str
    context: str
    source: str = "rules"


TRUST_SIGNALS = {
    Category.HEALTH_WELLNESS: "★★★★★ Top-rated wellness picks",
    Category.PET_SUPPLIES: "★★★★☆ Trusted pet brands",
    Category.HOUSEHOLD: "★★★★★ Bestsellers in household",
    Category.PERSONAL_CARE: "★★★★☆ Curated personal care",
    Category.BABY_CARE: "★★★★★ Parent-trusted brands",
    Category.SNACKS: "★★★★☆ Popular add-ons",
    Category.FROZEN: "★★★★☆ Quick freezer essentials",
}


class ExplainabilityLayer:
    """Phase 2: AI explainability — Grok LLM when enabled, rule templates as fallback."""

    def __init__(self, llm_client: GrokLLMClient | None = None) -> None:
        self.analyzer = PurchaseHistoryAnalyzer()
        self.llm = llm_client or GrokLLMClient()

    def generate(
        self,
        history: PurchaseHistory,
        recommended_category: Category,
        reason_tags: list[str] | None = None,
    ) -> Explanation:
        freq = self.analyzer.get_frequent_categories(history, top_n=2)
        dominant_day = self.analyzer.get_dominant_day(history)
        trust = TRUST_SIGNALS.get(
            recommended_category, "★★★★☆ Recommended for you"
        )

        llm_result = self.llm.generate_explanation(
            frequent_categories=[cat.value for cat, _ in freq],
            recommended_category=recommended_category.value,
            dominant_day=dominant_day,
            reason_tags=reason_tags,
        )

        if llm_result:
            return Explanation(
                headline=llm_result["headline"],
                reason=llm_result["reason"],
                trust_signal=trust,
                context=llm_result["context"],
                source="grok",
            )

        return self._rule_based_explanation(
            history, recommended_category, freq, dominant_day, trust
        )

    def _rule_based_explanation(
        self,
        history: PurchaseHistory,
        recommended_category: Category,
        freq: list[tuple[Category, int]],
        dominant_day: str | None,
        trust: str,
    ) -> Explanation:
        if freq:
            top_cat, count = freq[0]
            reason = (
                f"We noticed you buy {top_cat.value.lower()} frequently "
                f"({count} times recently)."
            )
        else:
            reason = "Based on your weekly grocery shopping patterns."

        if dominant_day:
            context = (
                f"You typically shop on {dominant_day}s. "
                f"Explore {recommended_category.value} — curated for busy professionals."
            )
        else:
            context = f"Discover {recommended_category.value} — personalized for you."

        headline = self._build_headline(recommended_category, freq)

        return Explanation(
            headline=headline,
            reason=reason,
            trust_signal=trust,
            context=context,
            source="rules",
        )

    def _build_headline(
        self,
        category: Category,
        freq: list[tuple[Category, int]],
    ) -> str:
        templates = {
            Category.HEALTH_WELLNESS: (
                "You purchase fruits regularly. Would you like Vitamin Gummies?"
            ),
            Category.PET_SUPPLIES: (
                "Based on your weekly grocery shopping, you may need pet treats before the weekend."
            ),
            Category.HOUSEHOLD: (
                "Complete your essentials — household items you might be running low on."
            ),
            Category.PERSONAL_CARE: (
                "Working professionals like you often explore personal care during quick shops."
            ),
        }

        if category in templates:
            return templates[category]

        if freq:
            return f"Because you frequently buy {freq[0][0].value.lower()}, try {category.value}."
        return f"Discover {category.value} — one tap to add."

    def bundle_suggestion(self, primary_category: Category) -> list[str]:
        """Feature 3: Bundle suggestions for complementary items."""
        bundles = {
            Category.SNACKS: ["Cold Drink", "Dip", "Chocolate"],
            Category.MILK: ["Bread", "Butter", "Cereal"],
            Category.FRUITS: ["Yogurt", "Granola", "Honey"],
            Category.BREAD: ["Jam", "Peanut Butter", "Cheese Spread"],
            Category.HEALTH_WELLNESS: ["Green Tea", "Protein Bar", "Multivitamin"],
        }
        return bundles.get(primary_category, ["Popular add-on", "Best seller"])
