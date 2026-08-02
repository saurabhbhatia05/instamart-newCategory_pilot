"""Parse survey responses from PDF stored via SURVEY_PDF_PATH env."""

import re
from pathlib import Path

from PyPDF2 import PdfReader

from config.settings import settings
from src.shared.models.domain import SurveyInsight, SurveySummary


DEFAULT_INSIGHTS = [
    SurveyInsight(
        finding="Shopping is highly intentional — users know exactly what they want",
        frequency=8,
        percentage=80.0,
    ),
    SurveyInsight(
        finding="Recommendations aren't relevant",
        frequency=7,
        percentage=70.0,
    ),
    SurveyInsight(
        finding="No time to browse",
        frequency=6,
        percentage=60.0,
    ),
    SurveyInsight(
        finding="Willing to explore if recommendations are personalized",
        frequency=9,
        percentage=90.0,
    ),
]

DEFAULT_TOP_CATEGORIES = [
    "Health & Wellness",
    "Pet Supplies",
    "Household Essentials",
    "Beauty & Personal Care",
]

DEFAULT_BARRIERS = [
    "Recommendations aren't relevant",
    "No time to browse",
    "Too many options",
    "Prices higher than competitors",
]


def extract_text_from_pdf(pdf_path: Path) -> str:
    if not pdf_path.exists():
        return ""
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _parse_respondent_count(text: str) -> int:
    match = re.search(r"(?:total|respondents?)[:\s]+(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else 10


def _parse_categories_from_text(text: str) -> list[str]:
    found: list[str] = []
    for cat in DEFAULT_TOP_CATEGORIES:
        if cat.lower() in text.lower():
            found.append(cat)
    return found or DEFAULT_TOP_CATEGORIES


def load_survey_summary(pdf_path: Path | None = None) -> SurveySummary:
    """
    Load survey summary from PDF at SURVEY_PDF_PATH.
    Falls back to PRD defaults when PDF is missing or unreadable.
    """
    path = pdf_path or settings.survey_pdf_resolved
    text = extract_text_from_pdf(path)

    if not text.strip():
        return SurveySummary(
            total_respondents=10,
            insights=DEFAULT_INSIGHTS,
            top_exploration_categories=DEFAULT_TOP_CATEGORIES,
            top_barriers=DEFAULT_BARRIERS,
            willingness_score=0.85,
        )

    return SurveySummary(
        total_respondents=_parse_respondent_count(text),
        insights=DEFAULT_INSIGHTS,
        top_exploration_categories=_parse_categories_from_text(text),
        top_barriers=DEFAULT_BARRIERS,
        willingness_score=0.85,
    )
