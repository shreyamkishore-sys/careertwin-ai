from datetime import datetime, timezone
from typing import Any

from app.data.markets import MARKET_CATALOG, MARKET_DATA_SOURCE

PROTOTYPE_LAST_UPDATED = datetime(2026, 10, 1, tzinfo=timezone.utc)
PROTOTYPE_CONFIDENCE = 0.25
MARKET_CURRENCIES = {entry["code"]: entry["currency"] for entry in MARKET_CATALOG}


def _signal(
    career_id: str,
    market_code: str,
    demand_index: float,
    demand_trend: str,
    salary_low: float,
    salary_high: float,
    salary_growth_rate: float,
    automation_exposure: float,
    emerging_skills: list[str],
    emerging_skill_tags: list[str],
    declining_skills: list[str],
    hiring_trend: str,
    market_growth: float,
    geographic_demand: dict[str, str],
    possible_transition: str,
) -> dict[str, Any]:
    return {
        "career_id": career_id,
        "market_code": market_code,
        "currency": MARKET_CURRENCIES[market_code],
        "job_demand": demand_label(demand_index),
        "demand_index": demand_index,
        "demand_trend": demand_trend,
        "salary_low": salary_low,
        "salary_high": salary_high,
        "salary_growth_rate": salary_growth_rate,
        "ai_impact": ai_label(automation_exposure),
        "automation_exposure": automation_exposure,
        "emerging_skills": emerging_skills,
        "emerging_skill_tags": emerging_skill_tags,
        "declining_skills": declining_skills,
        "hiring_trend": hiring_trend,
        "market_growth": market_growth,
        "geographic_demand": geographic_demand,
        "possible_transition": possible_transition,
        "data_source": MARKET_DATA_SOURCE,
        "data_confidence": PROTOTYPE_CONFIDENCE,
        "data_status": "prototype_illustrative",
        "last_updated": PROTOTYPE_LAST_UPDATED,
    }


def demand_label(index: float) -> str:
    if index >= 70:
        return "High"
    if index >= 45:
        return "Medium"
    return "Low"


def ai_label(exposure: float) -> str:
    if exposure >= 66:
        return "high"
    if exposure >= 36:
        return "medium"
    return "low"


# Every value below is synthetic demonstration data. These values intentionally
# carry low confidence and must be replaced by sourced observations before any
# external or decision-critical use.
CAREER_MARKET_SEED_DATA = [
    _signal("product-analyst", "IN", 78, "rising", 6, 10, 8.5, 42,
            ["Product analytics", "SQL", "AI literacy"], ["data_analysis", "coding", "problem_solving"],
            ["Manual spreadsheet reporting"], "rising", 6.2,
            {"Bengaluru": "high", "Hyderabad": "high", "Mumbai": "medium"}, "Product Manager or Product Operations"),
    _signal("product-manager", "IN", 72, "rising", 12, 20, 8.0, 38,
            ["Product strategy", "AI literacy", "Experimentation"], ["business_strategy", "communication", "data_analysis"],
            ["Roadmaps disconnected from outcomes"], "rising", 5.9,
            {"Bengaluru": "high", "Mumbai": "high", "Delhi NCR": "medium"}, "Senior Product Manager or Product Lead"),
    _signal("data-analyst", "IN", 76, "stable", 4, 8, 7.8, 55,
            ["AI-assisted analytics", "SQL", "BI tools"], ["data_analysis", "coding", "statistics"],
            ["Manual report compilation"], "stable", 5.8,
            {"Bengaluru": "high", "Hyderabad": "high", "Pune": "medium"}, "Analytics Engineer or Analytics Lead"),
    _signal("business-analyst", "IN", 68, "rising", 5, 9, 7.0, 34,
            ["Process analytics", "AI literacy", "Requirements design"], ["problem_solving", "data_analysis", "communication"],
            ["Manual requirements documentation"], "rising", 5.4,
            {"Bengaluru": "high", "Delhi NCR": "high", "Mumbai": "medium"}, "Strategy or Transformation Lead"),
    _signal("ux-researcher", "IN", 54, "stable", 5, 9, 6.0, 29,
            ["Mixed-method research", "Accessibility", "AI product evaluation"], ["research", "communication", "problem_solving"],
            ["Unmoderated survey-only research"], "stable", 3.5,
            {"Bengaluru": "high", "Mumbai": "medium", "Delhi NCR": "medium"}, "UX Research Lead or Product Strategy"),
    _signal("software-developer", "IN", 82, "rising", 5, 10, 9.2, 61,
            ["AI-assisted development", "Cloud security", "System design"], ["coding", "problem_solving", "statistics"],
            ["Routine code-only implementation"], "rising", 7.1,
            {"Bengaluru": "high", "Hyderabad": "high", "Pune": "high"}, "Staff Engineer or Engineering Manager"),
    _signal("project-manager", "IN", 64, "stable", 5, 9, 6.4, 25,
            ["AI-enabled planning", "Change management", "Data literacy"], ["organization", "communication", "problem_solving"],
            ["Manual status reporting"], "stable", 4.5,
            {"Mumbai": "high", "Delhi NCR": "medium", "Bengaluru": "medium"}, "Program Manager or Portfolio Lead"),
    _signal("marketing-strategist", "IN", 61, "rising", 4, 8, 6.8, 48,
            ["Marketing analytics", "AI content governance", "Experimentation"], ["data_analysis", "writing", "research"],
            ["Undifferentiated bulk content production"], "rising", 5.0,
            {"Mumbai": "high", "Bengaluru": "medium", "Delhi NCR": "medium"}, "Growth Marketing or Brand Strategy"),
    _signal("digital-marketing-manager", "IN", 66, "rising", 8, 16, 7.2, 60,
            ["AI campaign operations", "Marketing analytics", "Experiment design"], ["data_analysis", "writing", "research"],
            ["Manual campaign reporting"], "rising", 5.2,
            {"Mumbai": "high", "Bengaluru": "high", "Delhi NCR": "medium"}, "Growth Marketing or Marketing Director"),
    _signal("hr-analyst", "IN", 56, "stable", 5, 10, 6.3, 52,
            ["People analytics", "Data privacy", "AI literacy"], ["data_analysis", "spreadsheets", "communication"],
            ["Manual HR reporting"], "stable", 4.1,
            {"Bengaluru": "high", "Mumbai": "medium", "Delhi NCR": "medium"}, "People Analytics or HR Business Partner"),
    _signal("data-scientist", "IN", 63, "rising", 7, 14, 8.0, 61,
            ["Statistical modeling", "Data engineering", "AI literacy"], ["statistics", "data_analysis", "coding"],
            ["Unvalidated model experimentation"], "rising", 5.5,
            {"Bengaluru": "high", "Hyderabad": "high", "Pune": "medium"}, "Machine Learning or Product Analytics"),
    _signal("financial-analyst", "IN", 59, "stable", 5, 10, 6.5, 41,
            ["Financial modeling", "Data visualization", "AI literacy"], ["spreadsheets", "statistics", "communication"],
            ["Manual recurring reporting"], "stable", 4.0,
            {"Mumbai": "high", "Delhi NCR": "medium", "Bengaluru": "medium"}, "FP&A or Finance Business Partner"),
    _signal("management-consultant", "IN", 60, "stable", 8, 16, 7.0, 37,
            ["Structured problem solving", "Change management", "AI literacy"], ["problem_solving", "business_strategy", "communication"],
            ["Template-based research synthesis"], "stable", 4.5,
            {"Mumbai": "high", "Delhi NCR": "high", "Bengaluru": "medium"}, "Strategy or Transformation Lead"),
    _signal("product-analyst", "US", 75, "rising", 70000, 105000, 5.7, 42,
            ["Product analytics", "SQL", "AI literacy"], ["data_analysis", "coding", "problem_solving"],
            ["Manual spreadsheet reporting"], "rising", 4.8,
            {"San Francisco": "high", "New York": "high", "Austin": "medium"}, "Product Manager or Product Operations"),
    _signal("product-manager", "US", 73, "rising", 100000, 150000, 5.8, 38,
            ["Product strategy", "AI literacy", "Experimentation"], ["business_strategy", "communication", "data_analysis"],
            ["Roadmaps disconnected from outcomes"], "rising", 4.9,
            {"San Francisco": "high", "New York": "high", "Austin": "medium"}, "Senior Product Manager or Product Lead"),
    _signal("data-analyst", "US", 79, "stable", 60000, 90000, 5.2, 55,
            ["AI-assisted analytics", "SQL", "BI tools"], ["data_analysis", "coding", "statistics"],
            ["Manual report compilation"], "stable", 4.4,
            {"New York": "high", "Seattle": "high", "Chicago": "medium"}, "Analytics Engineer or Analytics Lead"),
    _signal("business-analyst", "US", 69, "stable", 65000, 95000, 4.9, 34,
            ["Process analytics", "AI literacy", "Requirements design"], ["problem_solving", "data_analysis", "communication"],
            ["Manual requirements documentation"], "stable", 4.1,
            {"New York": "high", "Washington DC": "high", "Chicago": "medium"}, "Strategy or Transformation Lead"),
    _signal("ux-researcher", "US", 52, "stable", 70000, 105000, 4.3, 29,
            ["Mixed-method research", "Accessibility", "AI product evaluation"], ["research", "communication", "problem_solving"],
            ["Unmoderated survey-only research"], "stable", 3.0,
            {"San Francisco": "high", "Seattle": "medium", "New York": "medium"}, "UX Research Lead or Product Strategy"),
    _signal("software-developer", "US", 81, "rising", 75000, 115000, 6.0, 61,
            ["AI-assisted development", "Cloud security", "System design"], ["coding", "problem_solving", "statistics"],
            ["Routine code-only implementation"], "rising", 6.2,
            {"San Francisco": "high", "Seattle": "high", "Austin": "high"}, "Staff Engineer or Engineering Manager"),
    _signal("project-manager", "US", 65, "stable", 65000, 100000, 4.7, 25,
            ["AI-enabled planning", "Change management", "Data literacy"], ["organization", "communication", "problem_solving"],
            ["Manual status reporting"], "stable", 3.9,
            {"New York": "high", "Washington DC": "medium", "Austin": "medium"}, "Program Manager or Portfolio Lead"),
    _signal("marketing-strategist", "US", 62, "rising", 55000, 85000, 5.1, 48,
            ["Marketing analytics", "AI content governance", "Experimentation"], ["data_analysis", "writing", "research"],
            ["Undifferentiated bulk content production"], "rising", 4.3,
            {"New York": "high", "Los Angeles": "high", "Chicago": "medium"}, "Growth Marketing or Brand Strategy"),
    _signal("digital-marketing-manager", "US", 67, "rising", 80000, 130000, 5.2, 60,
            ["AI campaign operations", "Marketing analytics", "Experiment design"], ["data_analysis", "writing", "research"],
            ["Manual campaign reporting"], "rising", 4.4,
            {"New York": "high", "Los Angeles": "high", "Austin": "medium"}, "Growth Marketing or Marketing Director"),
    _signal("hr-analyst", "US", 57, "stable", 65000, 100000, 4.7, 52,
            ["People analytics", "Data privacy", "AI literacy"], ["data_analysis", "spreadsheets", "communication"],
            ["Manual HR reporting"], "stable", 3.6,
            {"New York": "high", "Washington DC": "medium", "Chicago": "medium"}, "People Analytics or HR Business Partner"),
    _signal("data-scientist", "US", 64, "rising", 95000, 150000, 5.8, 61,
            ["Statistical modeling", "Data engineering", "AI literacy"], ["statistics", "data_analysis", "coding"],
            ["Unvalidated model experimentation"], "rising", 5.1,
            {"San Francisco": "high", "Seattle": "high", "New York": "medium"}, "Machine Learning or Product Analytics"),
    _signal("financial-analyst", "US", 60, "stable", 70000, 110000, 4.8, 41,
            ["Financial modeling", "Data visualization", "AI literacy"], ["spreadsheets", "statistics", "communication"],
            ["Manual recurring reporting"], "stable", 3.8,
            {"New York": "high", "Chicago": "high", "Boston": "medium"}, "FP&A or Finance Business Partner"),
    _signal("management-consultant", "US", 61, "stable", 90000, 160000, 5.0, 37,
            ["Structured problem solving", "Change management", "AI literacy"], ["problem_solving", "business_strategy", "communication"],
            ["Template-based research synthesis"], "stable", 4.1,
            {"New York": "high", "Washington DC": "high", "Chicago": "medium"}, "Strategy or Transformation Lead"),
]
