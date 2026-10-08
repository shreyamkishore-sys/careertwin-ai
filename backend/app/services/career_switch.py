from collections import deque

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.career_transitions import (
    CAREER_TRANSITION_EDGES,
    PREFERRED_TRANSITION_PATHS,
    TRANSITION_SKILLS,
    TransitionSkill,
)
from app.models import Career, CareerMarketData, StudentProfile
from app.schemas import (
    CareerRead,
    CareerSwitchInput,
    CareerSwitchRead,
    TransitionMarketRead,
    TransitionRoadmapStageRead,
    TransitionSalaryPointRead,
    TransitionSkillRead,
)
from app.services.market_service import market_records, market_scenario_record
from app.services.simulation import build_career_simulations
from app.services.profile_ratings import SKILL_KEYS, SKILL_TAG_TO_RATING, normalize_ratings

PROFILE_SKILL_LABELS = {
    "problem_solving": "Problem solving",
    "communication": "Communication",
    "spreadsheets": "Spreadsheets",
    "data_analysis": "Data analysis",
    "coding": "Coding",
    "design": "Design",
    "writing": "Writing",
    "research": "Research",
    "organization": "Organization",
    "teamwork": "Teamwork",
    "visual_design": "Visual design",
    "statistics": "Statistics",
}

LEARNED_SKILL_MAP = {
    "sql": {"data_analysis", "coding", "statistics"},
    "python": {"coding", "problem_solving", "data_analysis"},
    "product_strategy": {"interest:business_strategy"},
    "roadmapping": {"organization"},
    "stakeholder_management": {"communication", "teamwork"},
    "user_research": {"research"},
    "communication": {"communication"},
}

LEARNED_REQUIREMENT_MAP = {
    "sql": {"SQL / data tools"},
    "python": {"Programming"},
    "product_strategy": {"Product strategy"},
    "roadmapping": {"Roadmapping and prioritization", "Planning and organization"},
    "stakeholder_management": {
        "Stakeholder management",
        "Stakeholder alignment",
        "Stakeholder communication",
    },
    "user_research": {"User research"},
    "communication": {
        "Communication",
        "Data communication",
        "Research communication",
        "Stakeholder communication",
    },
}

RELEVANCE_TAGS = {
    "data-analyst": {"analytics", "problem_solving"},
    "product-analyst": {"analytics", "product_strategy", "problem_solving"},
    "business-analyst": {"business_strategy", "stakeholder_management", "problem_solving"},
    "software-developer": {"technical_fluency", "problem_solving"},
    "ux-researcher": {"user_research", "communication"},
    "project-manager": {"roadmapping", "stakeholder_management", "teamwork"},
    "marketing-strategist": {"user_research", "communication", "analytics"},
    "digital-marketing-manager": {"user_research", "communication", "analytics", "teamwork"},
    "hr-analyst": {"analytics", "communication", "teamwork", "business_strategy"},
    "data-scientist": {"technical_fluency", "analytics", "problem_solving"},
    "financial-analyst": {"analytics", "business_strategy", "problem_solving"},
    "management-consultant": {"business_strategy", "stakeholder_management", "problem_solving"},
    "product-manager": {"product_strategy", "roadmapping", "stakeholder_management"},
}

TARGET_RELEVANCE = {
    "product-analyst": {"analytics", "product_strategy", "problem_solving"},
    "product-manager": {"product_strategy", "roadmapping", "stakeholder_management"},
    "data-analyst": {"analytics", "problem_solving"},
    "business-analyst": {"business_strategy", "stakeholder_management", "problem_solving"},
    "software-developer": {"technical_fluency", "problem_solving"},
    "project-manager": {"roadmapping", "stakeholder_management", "teamwork"},
    "ux-researcher": {"user_research", "communication"},
    "marketing-strategist": {"user_research", "communication", "analytics"},
    "digital-marketing-manager": {"user_research", "communication", "analytics", "teamwork"},
    "hr-analyst": {"analytics", "communication", "teamwork", "business_strategy"},
    "data-scientist": {"technical_fluency", "analytics", "problem_solving"},
    "financial-analyst": {"analytics", "business_strategy", "problem_solving"},
    "management-consultant": {"business_strategy", "stakeholder_management", "problem_solving"},
}

SNAPSHOT_YEARS = (0, 3, 5, 7, 10)


def _simple_routes(current_id: str, target_id: str) -> list[list[str]]:
    routes: list[list[str]] = []
    queue: deque[list[str]] = deque([[current_id]])
    shortest: int | None = None
    while queue:
        path = queue.popleft()
        if shortest is not None and len(path) > shortest:
            continue
        last = path[-1]
        for adjacent in CAREER_TRANSITION_EDGES.get(last, []):
            if adjacent in path:
                continue
            candidate = [*path, adjacent]
            if adjacent == target_id:
                routes.append(candidate)
                shortest = len(candidate) if shortest is None else min(shortest, len(candidate))
            elif shortest is None or len(candidate) < shortest:
                queue.append(candidate)
    return routes


def _routes(current_id: str, target_id: str) -> tuple[list[str], list[list[str]]]:
    all_routes = _simple_routes(current_id, target_id)
    if not all_routes:
        raise ValueError(
            f"No supported transition path is configured from '{current_id}' to '{target_id}'."
        )
    preferred = PREFERRED_TRANSITION_PATHS.get((current_id, target_id))
    if preferred and all(
        right in CAREER_TRANSITION_EDGES.get(left, [])
        for left, right in zip(preferred, preferred[1:])
    ):
        primary = preferred
    else:
        primary = all_routes[0]
    alternatives = [route for route in all_routes if route != primary]
    if preferred and len(preferred) > 2:
        direct_route = [current_id, target_id]
        if target_id in CAREER_TRANSITION_EDGES.get(current_id, []) and direct_route not in alternatives:
            alternatives.insert(0, direct_route)
    return primary, alternatives[:3]


def _skill_evidence(
    requirement: TransitionSkill,
    profile: StudentProfile,
    current: Career,
    learned: list[str],
) -> TransitionSkillRead:
    profile_tags = set(profile.skills)
    learned_tags = set().union(*(LEARNED_SKILL_MAP[skill] for skill in learned)) if learned else set()
    direct = set(requirement["profile_skills"])
    partial = set(requirement["partial_skills"])
    profile_matches = direct & profile_tags
    learned_matches = direct & learned_tags
    learned_requirement_matches = [
        skill
        for skill in learned
        if requirement["label"] in LEARNED_REQUIREMENT_MAP[skill]
    ]
    partial_matches = partial & set(profile.skills)
    evidence = [PROFILE_SKILL_LABELS.get(skill, skill.replace("_", " ").title()) for skill in sorted(profile_matches)]
    evidence.extend(
        f"Assumed: {skill.replace('_', ' ')}"
        for skill in learned_requirement_matches
    )
    if learned_matches and not learned_requirement_matches:
        evidence.extend(
            f"Assumed: {skill.replace('_', ' ')}"
            for skill in learned
            if learned_matches & LEARNED_SKILL_MAP[skill]
        )
    interest_matches = set(requirement["profile_interests"]) & set(profile.interests)
    learned_interest_matches = (
        set(requirement["profile_interests"])
        & {tag.removeprefix("interest:") for tag in learned_tags if tag.startswith("interest:")}
    )
    interest_matches |= learned_interest_matches
    evidence.extend(f"Interest: {item.replace('_', ' ')}" for item in sorted(interest_matches))
    career_matches = set(current.relevant_skills) & (direct | partial)

    current_rating = None
    required_rating = None
    gap = None
    if getattr(profile, "skill_ratings", None):
        ratings = normalize_ratings(profile.skill_ratings, SKILL_KEYS)
        normalized_label = requirement["label"].lower()
        explicit: list[str] = []
        if "sql" in normalized_label:
            explicit = ["sql"]
        elif "python" in normalized_label or "programming" in normalized_label:
            explicit = ["python"]
        elif "ai literacy" in normalized_label:
            explicit = ["ai_literacy"]
        elif "product strategy" in normalized_label:
            explicit = ["product_thinking", "business_knowledge"]
        elif "product metrics" in normalized_label or "data analysis" in normalized_label:
            explicit = ["data_analysis", "statistics", "excel"]
        elif "communication" in normalized_label or "stakeholder" in normalized_label:
            explicit = ["communication", "presentation"]
        else:
            explicit = list(dict.fromkeys(SKILL_TAG_TO_RATING[tag] for tag in direct | partial if tag in SKILL_TAG_TO_RATING))
        if explicit:
            current_rating = round(sum(ratings[key] for key in explicit) / len(explicit))
            required_rating = 4
            gap = max(0, required_rating - current_rating)
            evidence.append(f"Profile proficiency: {current_rating}/5 · target level {required_rating}/5")

    if current_rating is not None and current_rating >= (required_rating or 4):
        status = "ready"
    elif learned_matches or learned_requirement_matches:
        status = "assumed"
    elif current_rating is not None and current_rating >= 2:
        status = "partially_transferable"
    elif current_rating is not None:
        status = "to_develop"
    elif profile_matches:
        status = "ready"
    elif partial_matches or interest_matches:
        status = "partially_transferable"
    else:
        status = "to_develop"
    if career_matches:
        evidence.append(f"Current {current.title} role skills")
    if not evidence and status == "partially_transferable":
        evidence.append(f"Related experience from {current.title}")
    return TransitionSkillRead(label=requirement["label"], status=status, evidence=evidence, current_rating=current_rating, required_rating=required_rating, gap=gap)


def _market_view(record: CareerMarketData) -> TransitionMarketRead:
    return TransitionMarketRead(
        job_demand=record.job_demand,
        demand_index=record.demand_index,
        demand_trend=record.demand_trend,
        ai_impact=record.ai_impact,
        automation_exposure=record.automation_exposure,
        emerging_skills=record.emerging_skills,
        salary_growth_rate=record.salary_growth_rate,
        data_status=record.data_status,
        data_source=record.data_source,
        data_confidence=record.data_confidence,
        last_updated=record.last_updated,
    )


def _salary_points(
    simulation,
    switch_simulation,
    market_code: str,
    switch_year: int | None = None,
    salary_growth_shift: float = 0,
) -> list[TransitionSalaryPointRead]:
    output = []
    for year in SNAPSHOT_YEARS:
        if switch_year is not None and year >= switch_year:
            source_year = min(10, year - switch_year)
            point = switch_simulation.years[source_year]
        else:
            point = simulation.years[year]
        multiplier = (1 + salary_growth_shift / 100) ** max(0, year - (switch_year or 0))
        precision = 1 if market_code == "IN" else 0
        low = round(point.salary_low * multiplier, precision)
        mid = round(point.salary_mid * multiplier, precision)
        high = round(point.salary_high * multiplier, precision)
        role = point.role
        if switch_year is not None and year >= switch_year:
            role = switch_simulation.years[source_year].role
        output.append(
            TransitionSalaryPointRead(
                year=year,
                role=role,
                salary_low=low,
                salary_mid=mid,
                salary_high=high,
            )
        )
    return output


def analyze_career_switch(
    session: Session,
    profile: StudentProfile,
    request: CareerSwitchInput,
) -> CareerSwitchRead:
    careers = {
        career.id: career
        for career in session.scalars(select(Career)).all()
    }
    current = careers.get(request.current_career_id)
    target = careers.get(request.target_career_id)
    if current is None:
        raise ValueError(f"Current career '{request.current_career_id}' is not in the career database.")
    if target is None:
        raise ValueError(f"Target career '{request.target_career_id}' is not in the career database.")
    target_profile = TRANSITION_SKILLS.get(target.id)
    if target_profile is None:
        raise ValueError(f"Transition requirements are not configured for '{target.title}'.")

    primary_route, alternatives = _routes(current.id, target.id)
    requirements = target_profile["requirements"]
    assert isinstance(requirements, list)
    skills = [
        _skill_evidence(requirement, profile, current, request.learned_skills)
        for requirement in requirements
    ]
    ready = [skill for skill in skills if skill.status == "ready"]
    assumed = [skill for skill in skills if skill.status == "assumed"]
    partial = [skill for skill in skills if skill.status == "partially_transferable"]
    missing = [skill for skill in skills if skill.status == "to_develop"]
    if profile.skill_ratings:
        scenario_profile_overlap = round(100 * sum(
            (1.0 if skill.status in {"ready", "assumed"} else skill.current_rating / (skill.required_rating or 4) if skill.current_rating else 0.0)
            for skill in skills
        ) / max(1, len(skills)), 1)
    else:
        scenario_profile_overlap = round(
            100 * (len(ready) + len(assumed) + 0.5 * len(partial)) / max(1, len(skills)),
            1,
        )
    current_role_coverage = 100 * sum(
        bool(
            set(current.relevant_skills)
            & (set(requirement["profile_skills"]) | set(requirement["partial_skills"]))
        )
        for requirement in requirements
    ) / max(1, len(requirements))
    overlap = round(scenario_profile_overlap * 0.7 + current_role_coverage * 0.3, 1)
    route_length = len(primary_route) - 1
    experience_relevance = max(
        45.0,
        min(95.0, 88.0 - max(0, route_length - 1) * 11 + min(request.years_before_switch, 5) * 3),
    )
    market_data = market_records(session, request.market)
    market_shift = 15 if request.what_if.increase_demand else -15 if request.what_if.decrease_demand else 0
    ai_shift = 15 if request.what_if.increase_ai_adoption else -15 if request.what_if.decrease_ai_adoption else 0
    current_market = market_scenario_record(
        market_data[current.id],
        demand_shift=market_shift,
        automation_shift=ai_shift,
        salary_growth_shift=(
            2 if request.what_if.increase_salary_growth
            else -2 if request.what_if.decrease_salary_growth
            else 0
        ),
    )
    target_market = market_scenario_record(
        market_data[target.id],
        demand_shift=market_shift,
        automation_shift=ai_shift,
        salary_growth_shift=(
            2 if request.what_if.increase_salary_growth
            else -2 if request.what_if.decrease_salary_growth
            else 0
        ),
    )
    skill_gap_score = round(100 * (
        sum((skill.gap or 0) / (skill.required_rating or 4) for skill in skills) / max(1, len(skills))
        if profile.skill_ratings else len(missing) / max(1, len(skills))
    ), 1)
    entry_barrier = 25.0 if target.id in {"product-manager", "project-manager"} else 20.0
    market_risk = round((100 - target_market.demand_index) * 0.5, 1)
    difficulty_score = round(
        skill_gap_score * 0.45
        + (100 - overlap) * 0.20
        + (100 - experience_relevance) * 0.20
        + entry_barrier * 0.10
        + market_risk * 0.05,
        1,
    )
    difficulty = "Easy" if difficulty_score < 30 else "Moderate" if difficulty_score < 60 else "Difficult"
    preparation_min = max(1, len(missing) * 2 - min(request.years_before_switch, 5))
    preparation_max = preparation_min + 6 + len(missing) * 2
    if not missing:
        preparation_min, preparation_max = 1, 3
    if request.what_if.learn_technical_skills:
        preparation_min = max(1, preparation_min - 2)
        preparation_max = max(preparation_min, preparation_max - 2)
    if request.what_if.willing_mba:
        preparation_max += 6

    career_list = [current, target]
    market, trajectories = build_career_simulations(career_list, request.market)
    trajectory_by_id = {item.career_id: item for item in trajectories}
    current_trajectory = trajectory_by_id[current.id]
    target_trajectory = trajectory_by_id[target.id]
    salary_growth_shift = (
        2 if request.what_if.increase_salary_growth
        else -2 if request.what_if.decrease_salary_growth
        else 0
    )

    roadmap_horizon = max(3, preparation_max)
    first_stage_end = max(1, (roadmap_horizon + 2) // 3)
    second_stage_start = first_stage_end + 1
    second_stage_end = max(second_stage_start, (2 * roadmap_horizon + 2) // 3)
    third_stage_start = second_stage_end + 1
    roadmap = [
        TransitionRoadmapStageRead(
            title="Build target-career skills",
            description="Practice the target skills still marked to develop; use the optional learning controls to model assumed skills.",
            minimum_month=1,
            maximum_month=first_stage_end,
        ),
        TransitionRoadmapStageRead(
            title="Create relevant project evidence",
            description="Build a portfolio project that demonstrates the target responsibilities and market-relevant emerging skills.",
            minimum_month=second_stage_start,
            maximum_month=second_stage_end,
        ),
        TransitionRoadmapStageRead(
            title="Gain adjacent experience and explore roles",
            description="Seek cross-functional assignments or intermediate roles on the configured route before pursuing the target role.",
            minimum_month=third_stage_start,
            maximum_month=max(third_stage_start, roadmap_horizon),
        ),
    ]
    years_text = (
        f"after {request.years_before_switch} year{'s' if request.years_before_switch != 1 else ''}"
        if request.years_before_switch
        else "immediately"
    )
    difficulty_explanation = (
        f"{difficulty} transition scenario: {len(ready)} of {len(skills)} target skill areas "
        f"are reflected in your profile, {len(assumed)} are assumed for this scenario, "
        f"{len(partial)} are partially transferable, "
        f"and {len(missing)} remain to develop. The selected experience window is {years_text}; "
        f"market demand is {target_market.job_demand.lower()}."
    )
    education = str(target_profile["education"])
    if request.willing_additional_education or request.what_if.willing_mba:
        education += " Your scenario indicates willingness to consider additional education; no degree-based salary premium is assumed."
    assumptions = [
        "Transition routes and target skill requirements are curated prototype data, not guaranteed hiring pathways.",
        "Preparation ranges are illustrative estimates and depend on study time, opportunity, and prior experience.",
        "Salary trajectories reuse the existing illustrative career simulations; future compensation is not predicted.",
        "Market signals are illustrative prototype data, not live or verified labor-market observations.",
    ]
    if request.years_before_switch:
        assumptions.append(
            f"The salary scenario follows the current-career curve through year {request.years_before_switch}, then the target-career curve from its starting stage."
        )
    if request.what_if.increase_demand or request.what_if.decrease_demand:
        assumptions.append("Demand What-If changes only the illustrative market demand index and trend context.")
    if request.what_if.increase_ai_adoption or request.what_if.decrease_ai_adoption:
        assumptions.append("AI-adoption What-If changes illustrative automation exposure; it does not imply job loss.")

    route_careers = [CareerRead.model_validate(careers[career_id]) for career_id in primary_route]
    alternative_careers = [
        [CareerRead.model_validate(careers[career_id]) for career_id in route]
        for route in alternatives
    ]
    current_relevance = RELEVANCE_TAGS.get(current.id, set())
    target_relevance = TARGET_RELEVANCE.get(target.id, set())
    shared_relevance = len(current_relevance & target_relevance)
    target_responsibilities = str(target_profile["responsibilities"])
    current_responsibilities = (
        f"{current.summary} Existing role skills: {', '.join(current.relevant_skills)}."
    )
    return CareerSwitchRead(
        current_career=CareerRead.model_validate(current),
        target_career=CareerRead.model_validate(target),
        market=market,
        data_status=target_market.data_status,
        current_market=_market_view(current_market),
        target_market=_market_view(target_market),
        route=route_careers,
        alternative_routes=alternative_careers,
        transition_difficulty=difficulty,
        difficulty_score=difficulty_score,
        difficulty_factors={
            "skill_gap": skill_gap_score,
            "skill_overlap": overlap,
            "experience_relevance": experience_relevance,
            "target_entry_barrier": entry_barrier,
            "market_demand_risk": market_risk,
        },
        difficulty_explanation=difficulty_explanation,
        experience_relevance="High" if experience_relevance >= 75 else "Medium" if experience_relevance >= 60 else "Low",
        experience_relevance_score=experience_relevance,
        skill_overlap=overlap,
        transferable_skills=ready,
        assumed_skills=assumed,
        partially_transferable_skills=partial,
        skills_to_develop=missing,
        preparation_min_months=preparation_min,
        preparation_max_months=preparation_max,
        roadmap=roadmap,
        education_guidance=education,
        stayed_salary=_salary_points(
            current_trajectory,
            target_trajectory,
            request.market,
            salary_growth_shift=salary_growth_shift,
        ),
        switched_salary=_salary_points(
            current_trajectory,
            target_trajectory,
            request.market,
            switch_year=request.years_before_switch,
            salary_growth_shift=salary_growth_shift,
        ),
        current_responsibilities=current_responsibilities,
        target_responsibilities=target_responsibilities,
        current_work_style=current.work_styles,
        target_work_style=target.work_styles,
        current_management_responsibility=(
            "Individual-contributor/analyst scope in the illustrative entry stages."
            if "analyst" in current.title.casefold()
            else "Responsibilities vary by role and seniority."
        ),
        target_management_responsibility=(
            "May include cross-functional leadership; formal people management is not assumed at entry."
            if target.id == "product-manager"
            else "Responsibilities and people-management scope vary by role and seniority."
        ),
        explanation=(
            f"This is a plausible {current.title} to {target.title} transition scenario, "
            f"not a prediction. Skill overlap combines the profile-based assessment (70%) "
            f"with current-role skill coverage (30%); "
            f"{shared_relevance} transition capability areas overlap between these career definitions."
        ),
        assumptions=assumptions,
    )
