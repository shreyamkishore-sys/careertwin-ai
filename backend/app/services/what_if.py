from app.models import Career, CareerMarketData, StudentProfile
from app.schemas import (
    CareerSimulationRead,
    CareerSimulationStage,
    CareerSimulationYear,
    ScenarioScoreEffect,
    CareerMarketSignalRead,
    WhatIfCareerResult,
    WhatIfComparisonRead,
    WhatIfScenario,
)
from app.services.career_twin import _factor_contributions
from app.services.market_service import (
    MARKET_SCORE_WEIGHT,
    combined_career_score,
    enrich_simulations_with_market,
    evaluate_market_fit,
    latest_market_update,
    market_scenario_record,
)
from app.services.simulation import build_career_simulations

MBA_ROLE_PATHS = {
    "product-analyst": {
        7: "Product Manager (MBA route)",
        10: "Product Director (MBA route)",
    },
    "business-analyst": {
        4: "Senior Business Analyst (MBA route)",
        7: "Strategy Lead (MBA route)",
        10: "Strategy Director (MBA route)",
    },
    "project-manager": {
        7: "Program Manager (MBA route)",
        10: "Portfolio Director (MBA route)",
    },
    "marketing-strategist": {
        7: "Marketing Manager (MBA route)",
        10: "Marketing Director (MBA route)",
    },
    "data-scientist": {
        7: "Analytics Lead (MBA route)",
        10: "Data Science Director (MBA route)",
    },
    "financial-analyst": {
        7: "Finance Manager (MBA route)",
        10: "Finance Director (MBA route)",
    },
    "management-consultant": {
        7: "Engagement Manager (MBA route)",
        10: "Principal Consultant (MBA route)",
    },
}


def _scenario_effects(career: Career, scenario: WhatIfScenario) -> list[ScenarioScoreEffect]:
    effects = []
    checks = (
        (
            "avoid_coding",
            scenario.avoid_coding,
            -16.0 if "coding" in career.relevant_skills else 4.0,
            "Coding exposure is listed in this career's local skill profile."
            if "coding" in career.relevant_skills
            else "The local career profile does not list coding as a relevant skill.",
            "Avoid coding",
        ),
        (
            "higher_salary",
            scenario.higher_salary,
            8.0 if "salary" in career.priorities else -4.0,
            "This career is tagged for earning potential in the local dataset."
            if "salary" in career.priorities
            else "Earning potential is not a tagged strength in the local dataset.",
            "Higher salary priority",
        ),
        (
            "work_life_balance",
            scenario.work_life_balance,
            8.0 if "work_life_balance" in career.priorities else -4.0,
            "This career is tagged for work-life balance in the local dataset."
            if "work_life_balance" in career.priorities
            else "Work-life balance is not a tagged strength in the local dataset.",
            "Work-life balance priority",
        ),
        (
            "remote_work",
            scenario.remote_work,
            7.0 if "remote_work" in career.priorities or "remote_ready" in career.work_styles else -4.0,
            "The local dataset tags this career as remote-friendly."
            if "remote_work" in career.priorities or "remote_ready" in career.work_styles
            else "Remote work is not tagged as a strength for this career.",
            "Remote-work priority",
        ),
        (
            "international_opportunities",
            scenario.international_opportunities,
            7.0 if "international_opportunities" in career.priorities else -3.0,
            "International opportunities are tagged for this career in the local dataset."
            if "international_opportunities" in career.priorities
            else "International opportunities are not tagged as a strength for this career.",
            "International opportunities",
        ),
        (
            "willing_mba",
            scenario.willing_mba,
            8.0 if career.id in MBA_ROLE_PATHS else 0.0,
            "The sample includes an alternative MBA route for this career."
            if career.id in MBA_ROLE_PATHS
            else "No MBA-specific route is defined for this career in the sample.",
            "Open to an MBA",
        ),
        (
            "learn_technical_skills",
            scenario.learn_technical_skills,
            9.0 if "coding" in career.relevant_skills else (
                6.0 if {"analytics", "technology"} & set(career.related_interests) else 0.0
            ),
            "Technical learning is listed as a relevant skill area for this career."
            if "coding" in career.relevant_skills or {"analytics", "technology"} & set(career.related_interests)
            else "The sample does not identify a technical-skill advantage for this career.",
            "Willing to learn technical skills",
        ),
        (
            "faster_growth",
            scenario.faster_growth,
            8.0 if "growth" in career.priorities else -4.0,
            "Career growth is tagged as a priority this path may support."
            if "growth" in career.priorities
            else "Career growth is not tagged as a strength for this career.",
            "Faster career growth",
        ),
    )
    for condition, enabled, points, explanation, label in checks:
        if enabled:
            effects.append(
                ScenarioScoreEffect(
                    condition=condition,
                    label=label,
                    points=points,
                    explanation=explanation,
                )
            )
    return effects


def _scenario_path(
    career: Career,
    baseline: CareerSimulationRead,
    scenario: WhatIfScenario,
    market_code: str,
    salary_growth_delta: float,
) -> tuple[CareerSimulationRead, bool, str]:
    years = list(baseline.years)
    stages = list(baseline.stages)
    explanations = []

    if scenario.faster_growth:
        accelerated_years = []
        for point in baseline.years:
            source_year = min(10, point.year + (1 if point.year > 0 else 0))
            source = baseline.years[source_year]
            accelerated_years.append(
                CareerSimulationYear(
                    year=point.year,
                    role=source.role,
                    salary_low=source.salary_low,
                    salary_mid=source.salary_mid,
                    salary_high=source.salary_high,
                )
            )
        accelerated_stages = []
        for stage in baseline.stages:
            accelerated_year = max(0, stage.year - 1)
            if accelerated_stages:
                accelerated_year = max(accelerated_stages[-1].year + 1, accelerated_year)
            accelerated_year = min(10, accelerated_year)
            accelerated_stages.append(
                CareerSimulationStage(
                    year=accelerated_year,
                    role=stage.role,
                    skills=stage.skills,
                )
            )
        years = accelerated_years
        stages = accelerated_stages
        explanations.append(
            "The faster-growth scenario advances the sample role and salary progression by about one year after the starting point. This is an illustrative what-if assumption, not a forecast."
        )

    mba_path = MBA_ROLE_PATHS.get(career.id) if scenario.willing_mba else None
    if mba_path:
        stages = [
            CareerSimulationStage(
                year=stage.year,
                role=mba_path.get(baseline_stage.year, stage.role),
                skills=stage.skills,
            )
            for baseline_stage, stage in zip(baseline.stages, stages)
        ]
        years = [
            CareerSimulationYear(
                year=point.year,
                role=next(
                    (stage.role for stage in reversed(stages) if stage.year <= point.year),
                    stages[0].role,
                ),
                salary_low=point.salary_low,
                salary_mid=point.salary_mid,
                salary_high=point.salary_high,
            )
            for point in years
        ]
        explanations.append(
            "The scenario shows an optional MBA-oriented role route where the sample includes one. Salary ranges are not given an MBA premium because the prototype has no defensible MBA salary-premium data."
        )

    if salary_growth_delta:
        precision = 1 if market_code == "IN" else 0
        years = [
            CareerSimulationYear(
                year=point.year,
                role=point.role,
                salary_low=round(
                    point.salary_low * (1 + salary_growth_delta / 100) ** point.year,
                    precision,
                ),
                salary_mid=round(
                    point.salary_mid * (1 + salary_growth_delta / 100) ** point.year,
                    precision,
                ),
                salary_high=round(
                    point.salary_high * (1 + salary_growth_delta / 100) ** point.year,
                    precision,
                ),
            )
            for point in years
        ]
        direction = "increases" if salary_growth_delta > 0 else "decreases"
        explanations.append(
            f"The illustrative salary scenario {direction} annual growth by "
            f"{abs(salary_growth_delta):g} percentage points relative to the local sample rate; "
            "the compounding is a what-if assumption, not a forecast."
        )

    market_only_changes = any(
        (
            scenario.increase_demand,
            scenario.decrease_demand,
            scenario.increase_ai_adoption,
            scenario.decrease_ai_adoption,
            scenario.emerging_skills_important,
        )
    )
    if market_only_changes:
        explanations.append(
            "Demand, AI-exposure, and emerging-skill assumptions update the market score and "
            "stage outlook; they do not invent a causal promotion or salary effect."
        )

    trajectory = CareerSimulationRead(
        career_id=baseline.career_id,
        career_title=baseline.career_title,
        category=baseline.category,
        years=years,
        stages=stages,
    )
    if explanations:
        return (
            trajectory,
            bool(scenario.faster_growth or mba_path or salary_growth_delta),
            " ".join(explanations),
        )

    reasons = []
    if scenario.avoid_coding and "coding" in career.relevant_skills:
        reasons.append("the role/skill path is unchanged even though coding appears in its local skill profile")
    if scenario.higher_salary:
        reasons.append("a salary preference changes fit only; it does not raise the salary estimates")
    if scenario.work_life_balance or scenario.remote_work or scenario.international_opportunities:
        reasons.append("these preferences change fit only because the sample has no modeled causal effect on role or salary progression")
    if scenario.learn_technical_skills:
        reasons.append("technical learning changes fit, but the sample does not model personal upskilling changing promotion dates")
    if any(
        (
            scenario.increase_demand,
            scenario.decrease_demand,
            scenario.increase_ai_adoption,
            scenario.decrease_ai_adoption,
            scenario.emerging_skills_important,
        )
    ):
        reasons.append(
            "demand, AI, and skill emphasis update the market outlook and fit score, but have no "
            "modeled causal effect on roles or salary progression in this prototype"
        )
    path_changed = bool(scenario.faster_growth or mba_path or salary_growth_delta)
    explanation = (
        "The role and salary path is unchanged"
        + (": " + "; ".join(reasons) if reasons else " because none of the selected conditions changes this sample progression")
        + "."
    )
    if market_only_changes:
        explanation += " Demand/AI/skill assumptions update the market outlook but do not invent role or salary causality."
    return baseline, path_changed, explanation


def compare_what_if(
    profile: StudentProfile,
    careers: list[Career],
    market_code: str,
    scenario: WhatIfScenario,
    market_data_records: dict[str, CareerMarketData],
) -> WhatIfComparisonRead:
    market, baseline_paths = build_career_simulations(careers, market_code)
    baseline_by_id = {path.career_id: path for path in baseline_paths}
    results = []
    for career in careers:
        base_path = baseline_by_id[career.id]
        market_record = market_data_records[career.id]
        profile_score = round(
            sum(factor.points for factor in _factor_contributions(profile, career)),
            1,
        )
        baseline_market_fit = evaluate_market_fit(market_record, profile.skills, profile_skill_ratings=profile.skill_ratings)
        baseline_score = combined_career_score(profile_score, baseline_market_fit.market_score)
        scenario_record = market_scenario_record(
            market_record,
            demand_shift=(
                15.0 if scenario.increase_demand else
                -15.0 if scenario.decrease_demand else
                0.0
            ),
            automation_shift=(
                15.0 if scenario.increase_ai_adoption else
                -15.0 if scenario.decrease_ai_adoption else
                0.0
            ),
            salary_growth_shift=(
                2.0 if scenario.increase_salary_growth else
                -2.0 if scenario.decrease_salary_growth else
                0.0
            ),
        )
        scenario_market_fit = evaluate_market_fit(
            scenario_record,
            profile.skills,
            emerging_skills_important=scenario.emerging_skills_important,
            profile_skill_ratings=profile.skill_ratings,
        )

        effects = _scenario_effects(career, scenario)
        current_record = market_record
        current_market_fit = baseline_market_fit
        current_emerging_emphasis = False
        market_controls = (
            (
                "increase_demand",
                scenario.increase_demand,
                15.0,
                0.0,
                0.0,
                "Increase demand",
                "Raises this career's illustrative demand index by 15 points, bounded to 0–100.",
            ),
            (
                "decrease_demand",
                scenario.decrease_demand,
                -15.0,
                0.0,
                0.0,
                "Decrease demand",
                "Lowers this career's illustrative demand index by 15 points, bounded to 0–100.",
            ),
            (
                "increase_ai_adoption",
                scenario.increase_ai_adoption,
                0.0,
                15.0,
                0.0,
                "Increase AI adoption",
                "Raises illustrative automation exposure by 15 points, bounded to 0–100.",
            ),
            (
                "decrease_ai_adoption",
                scenario.decrease_ai_adoption,
                0.0,
                -15.0,
                0.0,
                "Decrease AI adoption",
                "Lowers illustrative automation exposure by 15 points, bounded to 0–100.",
            ),
            (
                "increase_salary_growth",
                scenario.increase_salary_growth,
                0.0,
                0.0,
                2.0,
                "Increase salary growth",
                "Raises the illustrative annual salary growth assumption by 2 percentage points.",
            ),
            (
                "decrease_salary_growth",
                scenario.decrease_salary_growth,
                0.0,
                0.0,
                -2.0,
                "Decrease salary growth",
                "Lowers the illustrative annual salary growth assumption by 2 percentage points.",
            ),
        )
        for condition, enabled, demand_shift, ai_shift, salary_shift, label, explanation in market_controls:
            if not enabled:
                continue
            current_record = market_scenario_record(
                current_record,
                demand_shift=demand_shift,
                automation_shift=ai_shift,
                salary_growth_shift=salary_shift,
            )
            next_market_fit = evaluate_market_fit(current_record, profile.skills, profile_skill_ratings=profile.skill_ratings)
            effective_points = round(
                (next_market_fit.market_score - current_market_fit.market_score)
                * MARKET_SCORE_WEIGHT,
                1,
            )
            effects.append(
                ScenarioScoreEffect(
                    condition=condition,
                    label=label,
                    points=effective_points,
                    explanation=explanation,
                )
            )
            current_market_fit = next_market_fit

        if scenario.emerging_skills_important:
            next_market_fit = evaluate_market_fit(
                current_record,
                profile.skills,
                emerging_skills_important=True,
                profile_skill_ratings=profile.skill_ratings,
            )
            effective_points = round(
                (next_market_fit.market_score - current_market_fit.market_score)
                * MARKET_SCORE_WEIGHT,
                1,
            )
            effects.append(
                ScenarioScoreEffect(
                    condition="emerging_skills_important",
                    label="Emerging skills become more important",
                    points=effective_points,
                    explanation=(
                        "Raises the emerging-skill match weight from 10% to 25% of the market "
                        "alignment score; the displayed skill gap is based on your saved skills."
                    ),
                )
            )
            current_emerging_emphasis = True
            current_market_fit = next_market_fit

        scenario_market_fit = evaluate_market_fit(
            scenario_record,
            profile.skills,
            emerging_skills_important=current_emerging_emphasis,
            profile_skill_ratings=profile.skill_ratings,
        )
        scenario_score = round(
            min(100.0, max(
                0.0,
                baseline_score
                + sum(effect.points for effect in effects),
            )),
            1,
        )
        baseline = enrich_simulations_with_market(
            [base_path],
            {career.id: market_record},
        )[0]
        salary_growth_delta = round(
            scenario_record.salary_growth_rate - market_record.salary_growth_rate,
            1,
        )
        scenario_path, trajectory_changed, trajectory_explanation = _scenario_path(
            career,
            base_path,
            scenario,
            market_code,
            salary_growth_delta,
        )
        scenario_path = enrich_simulations_with_market(
            [scenario_path],
            {career.id: scenario_record},
        )[0]
        results.append(
            WhatIfCareerResult(
                career_id=career.id,
                career_title=career.title,
                category=career.category,
                baseline_score=baseline_score,
                scenario_score=scenario_score,
                score_change=round(scenario_score - baseline_score, 1),
                score_effects=effects,
                baseline_market_score=baseline_market_fit.market_score,
                scenario_market_score=scenario_market_fit.market_score,
                baseline_market=CareerMarketSignalRead.model_validate(market_record),
                scenario_market=CareerMarketSignalRead.model_validate(scenario_record),
                baseline_skill_gap=baseline_market_fit.skill_gap,
                scenario_skill_gap=scenario_market_fit.skill_gap,
                trajectory_changed=trajectory_changed,
                trajectory_explanation=trajectory_explanation,
                baseline_simulation=baseline,
                scenario_simulation=scenario_path,
            )
        )
    results.sort(key=lambda result: (-result.scenario_score, result.career_title.casefold()))
    return WhatIfComparisonRead(
        market=market,
        scenario=scenario,
        careers=results,
        score_basis=(
            "Before combines profile alignment (85%) and market alignment (15%). After applies each "
            "displayed What-If adjustment to the market-adjusted baseline and bounds the final score "
            "to 0–100. The deterministic rules use synthetic prototype data, not measured labor-market effects."
        ),
        trajectory_basis=(
            "Faster-growth, defined MBA-route, and salary-growth assumptions can change sample role or salary "
            "paths. Demand, AI, and skill scenarios update market scores and outlook; other conditions change "
            "fit only. Unmodeled causal effects are not invented."
        ),
        data_status="prototype_illustrative",
        market_last_updated=latest_market_update(list(market_data_records.values())),
    )
