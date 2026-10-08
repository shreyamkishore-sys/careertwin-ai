from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.ai_risk import AI_RISK_DATA, SKILL_LABELS, impact_label, resilience_score
from app.models import Career, CareerMarketData, StudentProfile
from app.schemas import (
    AIRiskAnalysisInput,
    AIRiskAnalysisRead,
    AIRiskCatalogCareerRead,
    AIRiskCatalogRead,
    AIRiskMarketRead,
    AIRiskScoreRead,
    AIRiskTaskRead,
    AIReadinessRead,
    AIReadinessSkillRead,
    CareerRead,
)
from app.services.market_service import (
    market_entry,
    market_intelligence,
    market_records,
    market_scenario_record,
)
from app.services.profile_ratings import SKILL_KEYS, SKILL_TAG_TO_RATING, ratings_for_profile

AI_RISK_ASSUMPTIONS = [
    "AI impact, automation exposure, resilience, and skill-change scores are deterministic illustrative scenario assessments, not employment predictions.",
    "Task lists are representative examples, not exhaustive descriptions of every role or workplace.",
    "New profiles include proficiency ratings; legacy profiles retain skill tags and use neutral defaults where levels were never recorded.",
    "A willingness-to-learn What-If assumes some future learning for scenario comparison; it does not certify that a skill has been acquired.",
    "Labor-market signals are supplied by the selected MarketDataProvider and currently use illustrative prototype records, not a live feed.",
]


def _score_read(config: dict[str, Any], automation_exposure: float, ai_shift: float) -> AIRiskScoreRead:
    impact_score = max(0, min(100, config["ai_impact_score"] + ai_shift))
    exposure = max(0, min(100, automation_exposure))
    resilience = resilience_score(config["resilience_components"], exposure)
    components = config["resilience_components"]
    reasons = sorted(components, key=lambda factor: components[factor], reverse=True)[:3]
    reason_text = ", ".join(factor.replace("_", " ") for factor in reasons)
    return AIRiskScoreRead(
        ai_impact_score=impact_score,
        impact_level=impact_label(impact_score),
        automation_exposure=exposure,
        ai_resilience_score=resilience,
        skill_change_score=config["skill_change_score"],
        opportunity_score=config["opportunity_score"],
        resilience_explanation=(
            f"Resilience combines human judgment, communication, strategic importance, leadership, "
            f"domain expertise, complexity, AI complementarity, and inverse task exposure. "
            f"The strongest configured factors for this career are {reason_text}; this describes "
            f"relative task characteristics, not immunity from change."
        ),
    )


def _market_read(record: CareerMarketData, market_code: str) -> AIRiskMarketRead:
    return AIRiskMarketRead(
        market=market_entry(market_code),
        job_demand=record.job_demand,
        demand_index=record.demand_index,
        demand_trend=record.demand_trend,
        ai_impact=record.ai_impact,
        automation_exposure=record.automation_exposure,
        hiring_trend=record.hiring_trend,
        emerging_skills=record.emerging_skills,
        data_source=record.data_source,
        data_confidence=record.data_confidence,
        data_status=record.data_status,
        last_updated=record.last_updated,
    )


def list_ai_risk_careers(session: Session, market_code: str) -> AIRiskCatalogRead:
    market_info = market_intelligence(session, market_code)
    records = market_records(session, market_code)
    careers = {
        career.id: career
        for career in session.scalars(select(Career).order_by(Career.title)).all()
    }
    output = []
    for career_id, config in AI_RISK_DATA.items():
        career = careers.get(career_id)
        record = records.get(career_id)
        if career is None or record is None:
            raise RuntimeError(
                f"AI risk data is incomplete for career '{career_id}' in market '{market_code}'."
            )
        score = _score_read(config, config["automation_exposure"], 0)
        output.append(
            AIRiskCatalogCareerRead(
                career_id=career_id,
                career_title=career.title,
                ai_impact_score=score.ai_impact_score,
                impact_level=score.impact_level,
                automation_exposure=score.automation_exposure,
                ai_resilience_score=score.ai_resilience_score,
                skill_change_score=score.skill_change_score,
                opportunity_score=score.opportunity_score,
                job_demand=record.job_demand,
                demand_trend=record.demand_trend,
                data_status=record.data_status,
                data_source=record.data_source,
                data_confidence=record.data_confidence,
                last_updated=record.last_updated,
            )
        )
    return AIRiskCatalogRead(
        market=market_info.market,
        provider=market_info.provider,
        data_status=market_info.data_status,
        last_updated=market_info.last_updated,
        careers=output,
    )


def _readiness(
    config: dict[str, Any],
    profile: StudentProfile,
    learn_technical_skills: bool,
    emerging_skills_important: bool,
) -> AIReadinessRead:
    profile_skills = set(profile.skills)
    numeric_profile = bool(getattr(profile, "skill_ratings", None))
    ratings = ratings_for_profile(profile, "skill_ratings", SKILL_KEYS, "skills", SKILL_TAG_TO_RATING)
    entries: list[dict[str, Any]] = []
    for label, skill_tags, weight, technical in config["future_skills"]:
        normalized_label = label.strip().lower().replace(" ", "_")
        direct_key = normalized_label if normalized_label in ratings else None
        if "ai_literacy" in normalized_label or "ai_product" in normalized_label or "ai_assisted" in normalized_label:
            direct_key = "ai_literacy"
        elif normalized_label in {"sql", "sql_and_data_validation"}:
            direct_key = "sql"
        elif normalized_label == "python":
            direct_key = "python"
        rating_keys = [direct_key] if direct_key else [SKILL_TAG_TO_RATING[tag] for tag in skill_tags if tag in SKILL_TAG_TO_RATING]
        current_rating = round(sum(ratings[key] for key in rating_keys) / len(rating_keys)) if rating_keys else 3
        required_rating = 4 if technical else 3
        matched = (current_rating >= required_rating) if numeric_profile else any(tag in profile_skills for tag in skill_tags)
        assumed = not matched and technical and learn_technical_skills
        entries.append(
            {
                "label": label,
                "status": "ready" if matched else "assumed" if assumed else "gap",
                "weight": weight,
                "technical": technical,
                "profile_tags": skill_tags,
                "current_rating": current_rating,
                "required_rating": required_rating,
                "gap": max(0, required_rating - current_rating),
                "readiness_points": min(current_rating / required_rating, 1.0),
            }
        )

    total_weight = sum(item["weight"] for item in entries) or 1.0
    baseline_points = sum(
        item["weight"] * (item["readiness_points"] if numeric_profile else 1.0)
        for item in entries if item["status"] == "ready"
    )
    if numeric_profile:
        baseline_points += sum(item["weight"] * item["readiness_points"] for item in entries if item["status"] == "gap")
    scenario_points = sum(
        item["weight"] if item["status"] == "assumed" else item["weight"] * (item["readiness_points"] if numeric_profile else 1.0)
        for item in entries if item["status"] in ({"ready", "assumed", "gap"} if numeric_profile else {"ready", "assumed"})
    )
    baseline_score = round(100 * baseline_points / total_weight)
    scenario_score = round(100 * scenario_points / total_weight)
    strengths = [
        item["label"] for item in entries if item["status"] == "ready" and (numeric_profile or not item["profile_tags"])
    ] + [
        SKILL_LABELS[tag]
        for tag in sorted(profile_skills)
        if any(item["status"] == "ready" and tag in item["profile_tags"] for item in entries)
    ]
    gaps = [item["label"] for item in entries if item["status"] == "gap"]
    assumed_skills = [item["label"] for item in entries if item["status"] == "assumed"]
    priorities = [item for item in entries if item["status"] == "gap"]
    priorities.sort(
        key=lambda item: (
            -(
                item["weight"]
                * (1.5 if emerging_skills_important and item["technical"] else 1.0)
            ),
            item["label"],
        )
    )
    return AIReadinessRead(
        baseline_score=baseline_score,
        scenario_score=scenario_score,
        strengths=list(dict.fromkeys(strengths)),
        gaps=gaps,
        assumed_skills=assumed_skills,
        learn_next=[item["label"] for item in priorities[:5]],
        skill_evidence=[
            AIReadinessSkillRead(**item)
            for item in entries
        ],
        explanation=(
            "Readiness uses saved skill proficiency ratings against configured future-skill levels; "
            "partial proficiency contributes proportionally. Older profiles use skill-tag matching "
            "with neutral rating fallbacks. Scenario-only learning assumptions are listed separately."
        ),
    )


def _task_category(exposure: float, judgment: float) -> str:
    if exposure >= 65 and judgment < 55:
        return "highly_automatable"
    if exposure >= 55 and judgment >= 60:
        return "ai_augmented"
    if exposure < 45 and judgment >= 70:
        return "human_centric"
    return "lower_priority"


def analyze_ai_risk(
    session: Session,
    career_id: str,
    profile: StudentProfile,
    request: AIRiskAnalysisInput,
) -> AIRiskAnalysisRead:
    config = AI_RISK_DATA.get(career_id)
    if config is None:
        raise ValueError(f"AI risk analysis is not configured for career '{career_id}'.")
    career = session.get(Career, career_id)
    if career is None:
        raise ValueError(f"Career '{career_id}' is not in the career database.")
    records = market_records(session, request.market)
    market_record = records.get(career_id)
    if market_record is None:
        raise RuntimeError(
            f"No market data is configured for career '{career_id}' in '{request.market}'."
        )

    ai_shift = (
        15 if request.what_if.increase_ai_adoption
        else -15 if request.what_if.decrease_ai_adoption
        else 0
    )
    scenario_record = market_scenario_record(
        market_record,
        automation_shift=ai_shift,
    )
    baseline = _score_read(config, config["automation_exposure"], 0)
    scenario = _score_read(
        config,
        max(0, min(100, config["automation_exposure"] + ai_shift)),
        ai_shift,
    )
    tasks = [
        AIRiskTaskRead(
            name=name,
            automation_exposure=max(0, min(100, exposure + ai_shift)),
            ai_assistance_potential=assistance,
            human_judgment=judgment,
            future_importance=importance,
            category=_task_category(
                max(0, min(100, exposure + ai_shift)),
                judgment,
            ),
            explanation=explanation,
        )
        for name, exposure, assistance, judgment, importance, explanation in config["tasks"]
    ]
    readiness = _readiness(
        config,
        profile,
        request.what_if.learn_technical_skills,
        request.what_if.emerging_skills_important,
    )
    effects = []
    if request.what_if.increase_ai_adoption:
        effects.append(
            "Higher AI-adoption scenario: modeled AI impact and task exposure rise by 15 points; resilience is recalculated using the same weighted factors."
        )
    elif request.what_if.decrease_ai_adoption:
        effects.append(
            "Lower AI-adoption scenario: modeled AI impact and task exposure fall by 15 points; resilience is recalculated using the same weighted factors."
        )
    if request.what_if.learn_technical_skills:
        effects.append(
            "The existing What-If setting assumes future learning for missing technical future skills; assumed skills are not treated as already acquired."
        )
    if request.what_if.emerging_skills_important:
        effects.append(
            "The existing emerging-skills setting reprioritizes technical/evolving skill gaps; it does not add skills to the saved profile."
        )
    if not effects:
        effects.append(
            "No AI-related What-If adjustments are active; the display uses the illustrative baseline scenario."
        )

    return AIRiskAnalysisRead(
        career=CareerRead.model_validate(career),
        baseline=baseline,
        scenario=scenario,
        tasks=tasks,
        future_skills=[item[0] for item in config["future_skills"]],
        resilient_skills=config["resilient_skills"],
        opportunities=config["opportunities"],
        risks=config["risks"],
        readiness=readiness,
        baseline_market=_market_read(market_record, request.market),
        scenario_market=_market_read(scenario_record, request.market),
        scenario_effects=effects,
        assumptions=AI_RISK_ASSUMPTIONS,
    )
