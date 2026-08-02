"""Grok LLM client for Phase 2 explainability (optional, with rule-based fallback)."""

import json
import logging
import re

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class GrokLLMClient:
    """
    Calls Grok (xAI) or Groq-compatible chat API when USE_LLM=true.
    API key is read from GROK_API_KEY or GROQ_API_KEY in .env.
    """

    def __init__(self) -> None:
        self.timeout = httpx.Timeout(4.0, connect=2.0)

    @property
    def is_available(self) -> bool:
        return settings.llm_enabled

    def generate_explanation(
        self,
        frequent_categories: list[str],
        recommended_category: str,
        dominant_day: str | None,
        reason_tags: list[str] | None = None,
    ) -> dict[str, str] | None:
        if not self.is_available:
            return None

        tags = ", ".join(reason_tags or [])
        day_hint = f"They usually shop on {dominant_day}s." if dominant_day else ""

        prompt = f"""You are the Smart Discovery Assistant for Swiggy Instamart.
Write a concise, personalized cross-category recommendation for a busy working professional (25-44).

Purchase habits: {", ".join(frequent_categories) or "weekly groceries"}
Recommend exploring: {recommended_category}
{day_hint}
Signals: {tags or "personalized discovery"}

Return ONLY valid JSON with keys:
- headline (max 20 words, conversational)
- reason (max 25 words, starts with "Because you..." or "We noticed...")
- context (max 20 words, time-saving angle)

Example headline: "You purchase fruits every Monday. Would you like Vitamin Gummies?"
"""

        try:
            response = httpx.post(
                f"{settings.llm_api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 220,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        except Exception as exc:
            logger.warning("Grok LLM explainability fallback: %s", exc)
            return None

    def _parse_json_response(self, content: str) -> dict[str, str] | None:
        match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            if all(k in data for k in ("headline", "reason", "context")):
                return {
                    "headline": str(data["headline"]).strip(),
                    "reason": str(data["reason"]).strip(),
                    "context": str(data["context"]).strip(),
                }
        except json.JSONDecodeError:
            return None
        return None
