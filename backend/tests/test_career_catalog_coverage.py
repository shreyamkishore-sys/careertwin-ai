import unittest
from datetime import datetime, timezone
from math import isfinite

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.data.ai_risk import AI_RISK_DATA
from app.data.career_simulations import CAREER_SIMULATION_DATA, SIMULATION_MARKETS
from app.data.career_transitions import CAREER_TRANSITION_EDGES, TRANSITION_SKILLS
from app.data.careers import CAREER_SEED_DATA
from app.data.market_data import CAREER_MARKET_SEED_DATA
from app.db.base import Base
from app.models import Career, CareerMarketData, StudentProfile
from app.schemas import AIRiskAnalysisInput, CareerRead, CareerSwitchInput, WhatIfScenario
from app.services.ai_risk import analyze_ai_risk, list_ai_risk_careers
from app.services.career_switch import RELEVANCE_TAGS, TARGET_RELEVANCE, analyze_career_switch
from app.services.career_twin import _factor_contributions, generate_career_twin
from app.services.market_service import market_records, seed_market_data
from app.services.profile_ratings import (
    CAREER_REQUIRED_RATINGS,
    PREFERENCE_KEYS,
    PRIORITY_KEYS,
    SKILL_KEYS,
    required_skill_ratings,
)
from app.services.simulation import build_career_simulations
from app.services.what_if import MBA_ROLE_PATHS, compare_what_if


EXPECTED_CAREERS = {
    "product-analyst", "data-analyst", "business-analyst", "product-manager",
    "data-scientist", "software-developer", "digital-marketing-manager", "hr-analyst",
    "financial-analyst", "management-consultant", "ux-researcher", "project-manager",
    "marketing-strategist",
}
NEW_CAREERS = {"data-scientist", "financial-analyst", "management-consultant"}


class CareerCatalogCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.careers = [Career(**item) for item in CAREER_SEED_DATA]
        self.session.add_all(self.careers)
        self.session.commit()
        seed_market_data(self.session)
        self.profile = StudentProfile(
            name="Nyra", education_level="undergraduate", field_of_study="CSBS",
            skills=["spreadsheets", "coding", "statistics", "communication", "problem_solving", "data_analysis", "research", "organization", "teamwork"],
            skill_ratings={key: 3 for key in SKILL_KEYS},
            interests=["analytics", "business_strategy", "technology", "research", "communication", "leadership"],
            work_preferences=["independent", "collaborative", "remote_ready", "structured"],
            preference_ratings={key: 3 for key in PREFERENCE_KEYS},
            career_priorities=["salary", "growth", "work_life_balance", "stability", "remote_work", "international_opportunities"],
            priority_ratings={key: 3 for key in PRIORITY_KEYS},
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(self.profile)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_master_catalog_and_dependent_configuration_coverage(self) -> None:
        catalog_ids = [career.id for career in self.careers]
        self.assertEqual(set(catalog_ids), EXPECTED_CAREERS)
        self.assertEqual(len(catalog_ids), len(set(catalog_ids)))
        self.assertEqual(set(CAREER_SIMULATION_DATA), set(catalog_ids))
        self.assertEqual(set(AI_RISK_DATA), set(catalog_ids))
        self.assertEqual(set(TRANSITION_SKILLS), set(catalog_ids))
        self.assertEqual(set(CAREER_TRANSITION_EDGES), set(catalog_ids))
        self.assertEqual(set(RELEVANCE_TAGS), set(catalog_ids))
        self.assertEqual(set(TARGET_RELEVANCE), set(catalog_ids))
        market_ids = {row["career_id"] for row in CAREER_MARKET_SEED_DATA}
        self.assertEqual(market_ids, set(catalog_ids))
        for career in self.careers:
            with self.subTest(career=career.id):
                self.assertTrue(career.title.strip())
                self.assertTrue(career.summary.strip())
                self.assertTrue(career.category.strip())
                self.assertTrue(career.starter_roles)
                self.assertTrue(career.relevant_skills)
                self.assertTrue(required_skill_ratings(career.id, career.relevant_skills))
                self.assertTrue(CAREER_TRANSITION_EDGES[career.id])
                self.assertTrue(all(target in catalog_ids for target in CAREER_TRANSITION_EDGES[career.id]))
                self.assertTrue(all(1 <= rating <= 5 for rating in required_skill_ratings(career.id, career.relevant_skills).values()))
        self.assertTrue(NEW_CAREERS.issubset(CAREER_REQUIRED_RATINGS))
        self.assertTrue(NEW_CAREERS.issubset(MBA_ROLE_PATHS))

    def test_career_fit_comparison_and_numeric_skill_targets_cover_catalog(self) -> None:
        twin = generate_career_twin(self.session, self.profile, "IN")
        by_id = {career.id: career for career in twin.career_options}
        self.assertEqual(set(by_id), EXPECTED_CAREERS)
        for career in self.careers:
            with self.subTest(career=career.id):
                match = by_id[career.id]
                self.assertTrue(isfinite(match.fit_score))
                self.assertTrue(0 <= match.fit_score <= 100)
                self.assertTrue(match.factor_contributions)
                self.assertTrue(match.skill_gaps is not None)
                self.assertTrue(all(1 <= gap.current_rating <= 5 and 1 <= gap.required_rating <= 5 for gap in match.skill_gaps))
                self.assertTrue(CareerRead.model_validate(career).title)
                required = required_skill_ratings(career.id, career.relevant_skills)
                key = next(iter(required))
                baseline = dict(self.profile.skill_ratings)
                self.profile.skill_ratings = {**baseline, key: 1}
                low_points = next(item.points for item in _factor_contributions(self.profile, career) if item.factor == "skills")
                self.profile.skill_ratings = {**baseline, key: 5}
                high_points = next(item.points for item in _factor_contributions(self.profile, career) if item.factor == "skills")
                self.assertGreaterEqual(high_points, low_points)
        self.profile.skill_ratings = {key: 3 for key in SKILL_KEYS}

    def test_simulation_market_what_if_and_education_roi_data_cover_catalog(self) -> None:
        for market_code in SIMULATION_MARKETS:
            with self.subTest(market=market_code):
                _, paths = build_career_simulations(self.careers, market_code)
                self.assertEqual({path.career_id for path in paths}, EXPECTED_CAREERS)
                for path in paths:
                    self.assertEqual(len(path.years), 11)
                    self.assertTrue(all(isfinite(point.salary_mid) and point.salary_low <= point.salary_mid <= point.salary_high for point in path.years))
                    self.assertTrue(all(point.salary_low >= 0 for point in path.years))
                # Education ROI reuses these career simulation records; verify all target IDs resolve.
                self.assertEqual({path.career_id for path in paths}, EXPECTED_CAREERS)
                records = market_records(self.session, market_code)
                self.assertEqual(set(records), EXPECTED_CAREERS)
                for career_id, record in records.items():
                    self.assertEqual(record.data_status, "prototype_illustrative")
                    self.assertLessEqual(record.salary_low, record.salary_high)
                    self.assertTrue(record.data_source and record.last_updated)
                comparison = compare_what_if(self.profile, self.careers, market_code, WhatIfScenario(), records)
                self.assertEqual({career.career_id for career in comparison.careers}, EXPECTED_CAREERS)
                for career in comparison.careers:
                    self.assertTrue(isfinite(career.baseline_score))
                mba_comparison = compare_what_if(
                    self.profile, self.careers, market_code,
                    WhatIfScenario(willing_mba=True), records,
                )
                mba_results = {career.career_id: career for career in mba_comparison.careers}
                for career_id in NEW_CAREERS:
                    result = mba_results[career_id]
                    self.assertTrue(result.trajectory_changed)
                    mba_stage = next(stage for stage in result.scenario_simulation.stages if stage.year == 7)
                    self.assertIn("MBA route", mba_stage.role)
                    self.assertEqual(
                        [point.salary_mid for point in result.baseline_simulation.years],
                        [point.salary_mid for point in result.scenario_simulation.years],
                    )

    def test_market_database_records_are_seeded_for_each_career_and_market(self) -> None:
        rows = list(self.session.scalars(select(CareerMarketData)))
        self.assertEqual(len(rows), len(EXPECTED_CAREERS) * len(SIMULATION_MARKETS))
        self.assertEqual({row.career_id for row in rows}, EXPECTED_CAREERS)
        self.assertEqual({row.market_code for row in rows}, set(SIMULATION_MARKETS))

    def test_ai_risk_catalog_and_personalized_analysis_cover_each_career(self) -> None:
        catalog = list_ai_risk_careers(self.session, "IN")
        self.assertEqual({item.career_id for item in catalog.careers}, EXPECTED_CAREERS)
        for career_id in sorted(EXPECTED_CAREERS):
            with self.subTest(career=career_id):
                result = analyze_ai_risk(
                    self.session, career_id, self.profile,
                    AIRiskAnalysisInput(profile_id=self.profile.id, market="IN", what_if=WhatIfScenario()),
                )
                self.assertTrue(0 <= result.baseline.ai_impact_score <= 100)
                self.assertTrue(0 <= result.baseline.automation_exposure <= 100)
                self.assertTrue(0 <= result.baseline.ai_resilience_score <= 100)
                self.assertTrue(result.tasks and result.future_skills and result.resilient_skills)
                self.assertEqual(result.baseline_market.data_status, "prototype_illustrative")

    def test_every_career_can_be_a_career_switch_source_and_target(self) -> None:
        edge_pairs = {(source, target) for source, targets in CAREER_TRANSITION_EDGES.items() for target in targets}
        sources = {source for source, _ in edge_pairs}
        targets = {target for _, target in edge_pairs}
        self.assertEqual(sources, EXPECTED_CAREERS)
        self.assertTrue(NEW_CAREERS.issubset(targets))
        for source, target in sorted(edge_pairs):
            with self.subTest(source=source, target=target):
                result = analyze_career_switch(
                    self.session, self.profile,
                    CareerSwitchInput(profile_id=self.profile.id, current_career_id=source, target_career_id=target, market="IN"),
                )
                self.assertEqual(result.current_career.id, source)
                self.assertEqual(result.target_career.id, target)
                self.assertIn(result.transition_difficulty, {"Easy", "Moderate", "Difficult"})
                self.assertTrue(result.roadmap)
                self.assertTrue(result.switched_salary)
                self.assertTrue(result.education_guidance)


if __name__ == "__main__":
    unittest.main()
