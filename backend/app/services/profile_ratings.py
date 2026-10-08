from __future__ import annotations

from typing import Any

SKILL_KEYS = (
    "excel", "sql", "python", "statistics", "communication", "business_knowledge",
    "presentation", "leadership", "problem_solving", "data_analysis", "product_thinking", "ai_literacy",
)
PRIORITY_KEYS = (
    "salary", "career_growth", "work_life_balance", "job_security", "remote_work",
    "international_opportunities", "management_potential", "creativity", "low_coding",
)
PREFERENCE_KEYS = (
    "coding", "analytical_work", "people_interaction", "creativity", "management",
    "remote_work", "travel", "structured_work", "problem_solving", "strategic_thinking",
)

SKILL_TAG_TO_RATING = {
    "spreadsheets": "excel", "coding": "python", "statistics": "statistics",
    "communication": "communication", "problem_solving": "problem_solving",
    "data_analysis": "data_analysis", "research": "product_thinking",
    "writing": "presentation", "organization": "leadership", "teamwork": "communication",
    "design": "product_thinking", "visual_design": "product_thinking",
}
PRIORITY_TAG_TO_RATING = {
    "salary": "salary", "growth": "career_growth", "work_life_balance": "work_life_balance",
    "stability": "job_security", "remote_work": "remote_work",
    "international_opportunities": "international_opportunities", "creativity": "creativity",
    "impact": "management_potential",
}
WORK_STYLE_TO_PREFERENCE = {
    "collaborative": "people_interaction", "independent": "analytical_work",
    "structured": "structured_work", "flexible": "strategic_thinking", "remote_ready": "remote_work",
}
SKILL_TAG_TO_LABEL = {
    "spreadsheets": "Excel", "coding": "Python / coding", "statistics": "Statistics",
    "communication": "Communication", "problem_solving": "Problem solving",
    "data_analysis": "Data analysis", "research": "Analytical work", "writing": "Presentation",
    "organization": "Leadership / organization", "teamwork": "Communication",
    "design": "Product thinking", "visual_design": "Product thinking",
}
CAREER_REQUIRED_RATINGS: dict[str, dict[str, int]] = {
    "product-analyst": {"excel": 4, "sql": 4, "python": 2, "statistics": 3, "communication": 4, "business_knowledge": 4, "presentation": 3, "leadership": 3, "problem_solving": 4, "data_analysis": 4, "product_thinking": 4, "ai_literacy": 3},
    "business-analyst": {"excel": 4, "sql": 2, "python": 1, "statistics": 3, "communication": 4, "business_knowledge": 4, "presentation": 4, "leadership": 3, "problem_solving": 4, "data_analysis": 3, "product_thinking": 3, "ai_literacy": 3},
    "data-analyst": {"excel": 4, "sql": 4, "python": 3, "statistics": 4, "communication": 3, "business_knowledge": 3, "presentation": 3, "leadership": 2, "problem_solving": 4, "data_analysis": 4, "product_thinking": 2, "ai_literacy": 4},
    "data-scientist": {"excel": 2, "sql": 3, "python": 4, "statistics": 4, "communication": 3, "business_knowledge": 3, "presentation": 3, "leadership": 2, "problem_solving": 4, "data_analysis": 4, "product_thinking": 2, "ai_literacy": 4},
    "financial-analyst": {"excel": 4, "sql": 2, "python": 2, "statistics": 3, "communication": 4, "business_knowledge": 4, "presentation": 3, "leadership": 2, "problem_solving": 4, "data_analysis": 3, "product_thinking": 1, "ai_literacy": 3},
    "management-consultant": {"excel": 3, "sql": 1, "python": 1, "statistics": 3, "communication": 4, "business_knowledge": 4, "presentation": 4, "leadership": 4, "problem_solving": 5, "data_analysis": 3, "product_thinking": 3, "ai_literacy": 3},
}


def required_skill_ratings(career_id: str, relevant_tags: list[str]) -> dict[str, int]:
    configured = CAREER_REQUIRED_RATINGS.get(career_id, {})
    derived: dict[str, int] = {}
    for tag in relevant_tags:
        key = SKILL_TAG_TO_RATING.get(tag)
        if key:
            derived[key] = max(derived.get(key, 1), 4 if key in {"data_analysis", "statistics", "python"} else 3)
    return {**derived, **configured}


def _number(value: Any, fallback: int = 3) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        if isinstance(value, str):
            label = value.strip().lower()
            if label in {"low", "beginner", "strongly prefer low/no coding"}:
                return 1
            if label in {"somewhat low", "basic", "prefer low coding"}:
                return 2
            if label in {"medium", "moderate", "intermediate", "comfortable with some coding"}:
                return 3
            if label in {"high", "strong", "comfortable with technical work"}:
                return 4
            if label in {"very high", "advanced", "enjoy coding/technical work"}:
                return 5
        return fallback
    return number if 1 <= number <= 5 else fallback


def normalize_ratings(value: Any, keys: tuple[str, ...], defaults: dict[str, int] | None = None) -> dict[str, int]:
    values = value if isinstance(value, dict) else {}
    defaults = defaults or {}
    return {key: _number(values.get(key, defaults.get(key, 3)), defaults.get(key, 3)) for key in keys}


def ratings_for_profile(profile: Any, field: str, keys: tuple[str, ...], legacy_field: str | None = None, mapping: dict[str, str] | None = None) -> dict[str, int]:
    saved = getattr(profile, field, None)
    if isinstance(saved, dict) and saved:
        return normalize_ratings(saved, keys)
    defaults = {key: 3 for key in keys}
    if legacy_field and mapping:
        for tag in (getattr(profile, legacy_field, None) or []):
            key = mapping.get(tag)
            if key in defaults:
                defaults[key] = 4
    return defaults


def skill_rating(profile: Any, skill_tag: str) -> int:
    ratings = ratings_for_profile(profile, "skill_ratings", SKILL_KEYS, "skills", SKILL_TAG_TO_RATING)
    key = SKILL_TAG_TO_RATING.get(skill_tag)
    return ratings.get(key, 3) if key else 3
