from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Career, CareerMarketData, CareerTwin, StudentProfile
from app.schemas import (
    CareerMarketSignalRead,
    CareerMatchRead,
    CareerRead,
    CareerTwinRead,
    FitFactorContribution,
    StudentProfileRead,
)
from app.services.market_service import (
    MARKET_SCORE_WEIGHT,
    PROFILE_SCORE_WEIGHT,
    combined_career_score,
    evaluate_market_fit,
    latest_market_update,
    market_entry,
    market_records,
)
from app.services.profile_ratings import (
    CAREER_REQUIRED_RATINGS,
    PREFERENCE_KEYS,
    PRIORITY_KEYS,
    SKILL_KEYS,
    SKILL_TAG_TO_LABEL,
    SKILL_TAG_TO_RATING,
    PRIORITY_TAG_TO_RATING,
    WORK_STYLE_TO_PREFERENCE,
    normalize_ratings,
    ratings_for_profile,
    required_skill_ratings,
)
from app.services.development_plan import build_development_plan

INTEREST_LABELS = {
    "analytics": "analytical problem-solving",
    "business_strategy": "business strategy",
    "technology": "technology",
    "design_creativity": "design and creative work",
    "helping_people": "helping people",
    "communication": "communication",
    "leadership": "leadership",
    "research": "research",
}

SKILL_LABELS = {
    "problem_solving": "problem-solving",
    "communication": "communication",
    "spreadsheets": "spreadsheet analysis",
    "data_analysis": "data analysis",
    "coding": "coding",
    "design": "design",
    "writing": "writing",
    "research": "research",
    "organization": "organization",
    "teamwork": "teamwork",
    "visual_design": "visual design",
    "statistics": "statistics",
}

WORK_STYLE_LABELS = {
    "collaborative": "collaborative work",
    "independent": "independent work",
    "structured": "structured work",
    "flexible": "a flexible environment",
    "remote_ready": "remote-friendly work",
}

PRIORITY_LABELS = {
    "salary": "earning potential",
    "work_life_balance": "work-life balance",
    "growth": "career growth",
    "remote_work": "remote-work options",
    "stability": "stability",
    "impact": "meaningful impact",
    "international_opportunities": "international opportunities",
    "creativity": "creative work",
}

FIT_FACTORS = (
    {
        "factor": "interests",
        "label": "Interests",
        "weight": 40.0,
        "profile_attribute": "interests",
        "career_attribute": "related_interests",
        "labels": INTEREST_LABELS,
    },
    {
        "factor": "skills",
        "label": "Skills",
        "weight": 30.0,
        "profile_attribute": "skills",
        "career_attribute": "relevant_skills",
        "labels": SKILL_LABELS,
    },
    {
        "factor": "work_preferences",
        "label": "Work preferences",
        "weight": 15.0,
        "profile_attribute": "work_preferences",
        "career_attribute": "work_styles",
        "labels": WORK_STYLE_LABELS,
    },
    {
        "factor": "career_priorities",
        "label": "Career priorities",
        "weight": 15.0,
        "profile_attribute": "career_priorities",
        "career_attribute": "priorities",
        "labels": PRIORITY_LABELS,
    },
)


def _factor_contributions(
    profile: StudentProfile,
    career: Career,
) -> list[FitFactorContribution]:
    contributions = []
    for factor in FIT_FACTORS:
        selected = getattr(profile, factor["profile_attribute"])
        career_tags = set(getattr(career, factor["career_attribute"]))
        rating_points: float | None = None
        matched_tags = [tag for tag in selected if tag in career_tags]
        unmatched_tags = [tag for tag in selected if tag not in career_tags]
        if factor["factor"] == "skills" and getattr(profile, "skill_ratings", None):
            ratings = normalize_ratings(profile.skill_ratings, SKILL_KEYS)
            required = required_skill_ratings(career.id, career.relevant_skills)
            values = list(required.items())
            if values:
                rating_points = factor["weight"] * sum(min(ratings[key], required_rating) / required_rating for key, required_rating in values) / len(values)
                matched_tags = [key for key, required_rating in values if ratings[key] >= required_rating]
                unmatched_tags = [key for key, required_rating in values if ratings[key] < required_rating]
        elif factor["factor"] == "career_priorities" and getattr(profile, "priority_ratings", None):
            ratings = normalize_ratings(profile.priority_ratings, PRIORITY_KEYS)
            matched_keys = [PRIORITY_TAG_TO_RATING[tag] for tag in career_tags if tag in PRIORITY_TAG_TO_RATING]
            matched_keys.extend(("low_coding", "management_potential"))
            if matched_keys:
                matched_keys = list(dict.fromkeys(matched_keys))
                aligned_values = {
                    key: (6 - ratings[key] if "coding" in career.relevant_skills else ratings[key]) if key == "low_coding"
                    else (ratings[key] if "leadership" in career.related_interests or "growth" in career.priorities else 6 - ratings[key]) if key == "management_potential"
                    else ratings[key]
                    for key in matched_keys
                }
                rating_points = factor["weight"] * sum(aligned_values.values()) / (5 * len(matched_keys))
                matched_tags = [key for key in matched_keys if aligned_values[key] >= 4]
                unmatched_tags = [key for key in matched_keys if aligned_values[key] < 4]
        elif factor["factor"] == "work_preferences" and getattr(profile, "preference_ratings", None):
            ratings = normalize_ratings(profile.preference_ratings, PREFERENCE_KEYS)
            matched_keys = [WORK_STYLE_TO_PREFERENCE[tag] for tag in career_tags if tag in WORK_STYLE_TO_PREFERENCE]
            if "analytics" in career.related_interests:
                matched_keys.append("analytical_work")
            if "leadership" in career.related_interests:
                matched_keys.append("management")
            if "business_strategy" in career.related_interests:
                matched_keys.append("strategic_thinking")
            matched_keys.append("coding")
            if matched_keys:
                matched_keys = list(dict.fromkeys(matched_keys))
                aligned_values = {key: (ratings[key] if "coding" in career.relevant_skills else 6 - ratings[key]) if key == "coding" else ratings[key] for key in matched_keys}
                rating_points = factor["weight"] * sum(aligned_values.values()) / (5 * len(matched_keys))
                matched_tags = [key for key in matched_keys if aligned_values[key] >= 4]
                unmatched_tags = [key for key in matched_keys if aligned_values[key] < 4]
        matched_count = len(matched_tags)
        selected_count = len(selected) if rating_points is None else len(matched_tags) + len(unmatched_tags)
        points = rating_points if rating_points is not None else (
            round(factor["weight"] * matched_count / selected_count, 1)
            if selected_count
            else 0.0
        )
        if rating_points is not None:
            explanation = (
                f"{matched_count} of {selected_count} mapped requirements meet target proficiency. "
                f"Current 1–5 ratings contribute {points:g} of {factor['weight']:g} available points."
            )
        elif selected_count:
            explanation = (
                f"{matched_count} of {selected_count} selected "
                f"{factor['label'].lower()} match this career "
                f"({points:g} of {factor['weight']:g} available points)."
            )
        else:
            explanation = f"No {factor['label'].lower()} were selected, so this factor adds no points."
        contributions.append(
            FitFactorContribution(
                factor=factor["factor"],
                label=factor["label"],
                weight=factor["weight"],
                points=points,
                matched_count=matched_count,
                selected_count=selected_count,
        matched_items=[factor["labels"].get(tag, SKILL_TAG_TO_LABEL.get(tag, tag.replace("_", " "))) for tag in matched_tags],
        unmatched_items=[factor["labels"].get(tag, SKILL_TAG_TO_LABEL.get(tag, tag.replace("_", " "))) for tag in unmatched_tags],
                explanation=explanation,
            )
        )
    return contributions


def _match_reasons(profile: StudentProfile, career: Career) -> list[str]:
    reasons = [
        f"Connects with your interest in {INTEREST_LABELS[tag]}"
        for tag in profile.interests
        if tag in career.related_interests
    ]
    reasons.extend(
        f"Builds on your {SKILL_LABELS[tag]} skill"
        for tag in profile.skills
        if tag in career.relevant_skills
    )
    reasons.extend(
        f"Reflects your preference for {WORK_STYLE_LABELS[tag]}"
        for tag in profile.work_preferences
        if tag in career.work_styles
    )
    reasons.extend(
        f"May support your priority for {PRIORITY_LABELS[tag]}"
        for tag in profile.career_priorities
        if tag in career.priorities
    )
    return reasons


def _career_card(
    career: Career,
    profile: StudentProfile,
    recommended_ids: set[str],
    market_data: CareerMarketData,
) -> CareerMatchRead:
    contributions = _factor_contributions(profile, career)
    profile_score = round(sum(contribution.points for contribution in contributions), 1)
    market_fit = evaluate_market_fit(market_data, profile.skills, profile_skill_ratings=profile.skill_ratings)
    market_outlook = CareerMarketSignalRead.model_validate(market_data)
    ratings = ratings_for_profile(profile, "skill_ratings", SKILL_KEYS, "skills", SKILL_TAG_TO_RATING)
    skill_requirements = []
    skill_gaps = []
    for skill_key, required_rating in required_skill_ratings(career.id, career.relevant_skills).items():
        current_rating = ratings[skill_key]
        skill_requirements.append({
            "skill_key": skill_key,
            "skill": skill_key.replace("_", " ").title(),
            "current_rating": current_rating,
            "required_rating": required_rating,
        })
        if current_rating < required_rating:
            skill_gaps.append({
                "skill": skill_key.replace("_", " ").title(),
                "current_rating": current_rating,
                "required_rating": required_rating,
                "gap": required_rating - current_rating,
            })
    fit_score = combined_career_score(profile_score, market_fit.market_score)
    return CareerMatchRead(
        **CareerRead.model_validate(career).model_dump(),
        match_reasons=_match_reasons(profile, career),
        is_recommended=career.id in recommended_ids,
        fit_score=fit_score,
        profile_fit_score=profile_score,
        market_fit_score=market_fit.market_score,
        market_fit_adjustment=round(fit_score - profile_score, 1),
        market_explanation=market_fit.explanation,
        market_skill_gap=market_fit.skill_gap,
        skill_requirements=skill_requirements,
        skill_gaps=skill_gaps,
        development_plan=build_development_plan(fit_score, skill_requirements).model_dump(),
        market_outlook=market_outlook,
        factor_contributions=contributions,
    )


def generate_career_twin(
    session: Session,
    profile: StudentProfile,
    market_code: str = "IN",
) -> CareerTwinRead:
    careers = list(session.scalars(select(Career).order_by(Career.title)))
    if not careers:
        raise RuntimeError("The local career catalog is empty; database seeding did not complete.")

    selected_market = market_entry(market_code)
    market_data = market_records(session, market_code)
    missing_market_records = sorted(
        career.id for career in careers if career.id not in market_data
    )
    if missing_market_records:
        raise RuntimeError(
            f"Market '{market_code}' data is not configured for: "
            + ", ".join(missing_market_records)
        )

    def career_score(career: Career) -> float:
        profile_score = sum(
            contribution.points
            for contribution in _factor_contributions(profile, career)
        )
        market_score = evaluate_market_fit(market_data[career.id], profile.skills, profile_skill_ratings=profile.skill_ratings).market_score
        return combined_career_score(profile_score, market_score)

    ranked_careers = sorted(
        careers,
        key=lambda career: (
            -career_score(career),
            career.title.casefold(),
        ),
    )
    recommended = ranked_careers[:3]
    recommended_ids = {career.id for career in recommended}
    overview = (
        f"Your CareerTwin is shaped by your interest in "
        f"{', '.join(INTEREST_LABELS[tag] for tag in profile.interests[:2])}, "
        f"your {profile.education_level.replace('_', ' ')} background in {profile.field_of_study}, "
        "and the priorities you chose. Scores combine your profile alignment (85%) with an "
        "illustrative local market alignment (15%). Market inputs are synthetic prototype data, "
        "not labor-market observations. Scores are not probabilities, predictions, or guarantees."
    )

    twin = session.scalar(
        select(CareerTwin).where(CareerTwin.student_profile_id == profile.id)
    )
    if twin is None:
        twin = CareerTwin(
            student_profile_id=profile.id,
            overview=overview,
            recommended_career_ids=[career.id for career in recommended],
            generated_at=datetime.now(timezone.utc),
        )
        session.add(twin)
    else:
        twin.overview = overview
        twin.recommended_career_ids = [career.id for career in recommended]
        twin.generated_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(twin)

    return CareerTwinRead(
        id=twin.id,
        generated_at=twin.generated_at,
        overview=twin.overview,
        profile=StudentProfileRead.model_validate(profile),
        market=selected_market,
        market_data_status="prototype_illustrative",
        market_last_updated=latest_market_update(list(market_data.values())),
        score_basis=(
            f"Career fit = {PROFILE_SCORE_WEIGHT * 100:g}% profile alignment + "
            f"{MARKET_SCORE_WEIGHT * 100:g}% local market alignment. The profile factor "
            "weights remain interests 40, skills 30, work preferences 15, and priorities 15. "
            "Market alignment is a deterministic weighted score based on the displayed "
            "illustrative demand, growth, hiring, AI-exposure, and emerging-skill signals."
        ),
        recommended_careers=[
            _career_card(career, profile, recommended_ids, market_data[career.id])
            for career in ranked_careers
            if career.id in recommended_ids
        ],
        career_options=[
            _career_card(career, profile, recommended_ids, market_data[career.id])
            for career in ranked_careers
        ],
    )
