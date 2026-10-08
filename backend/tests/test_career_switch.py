import unittest
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import run_career_switch
from app.data.careers import CAREER_SEED_DATA
from app.db.base import Base
from app.models import Career, StudentProfile, User
from app.schemas import CareerSwitchInput, WhatIfScenario
from app.services.career_switch import analyze_career_switch
from app.services.market_service import seed_market_data


class CareerSwitchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.session.add_all(Career(**career) for career in CAREER_SEED_DATA)
        self.session.commit()
        seed_market_data(self.session)
        self.user = User(name="Nyra", email="nyra@example.com", password_hash="test-only", created_at=datetime.now(timezone.utc))
        self.session.add(self.user)
        self.session.commit()
        self.profile = StudentProfile(
            user_id=self.user.id,
            name="Nyra",
            education_level="undergraduate",
            field_of_study="Economics",
            skills=["data_analysis", "communication", "spreadsheets"],
            interests=["analytics", "business_strategy", "communication"],
            work_preferences=["collaborative", "structured"],
            career_priorities=["growth", "impact"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(self.profile)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def request(self, **overrides: object) -> CareerSwitchInput:
        values: dict[str, object] = {
            "profile_id": self.profile.id,
            "current_career_id": "data-analyst",
            "target_career_id": "product-manager",
            "market": "IN",
        }
        values.update(overrides)
        return CareerSwitchInput(**values)

    def test_demo_route_uses_configured_intermediate_and_direct_alternative(self) -> None:
        result = analyze_career_switch(self.session, self.profile, self.request())

        self.assertEqual(
            [career.id for career in result.route],
            ["data-analyst", "product-analyst", "product-manager"],
        )
        self.assertIn(
            ["data-analyst", "product-manager"],
            [[career.id for career in route] for route in result.alternative_routes],
        )
        self.assertIn("not a prediction", result.explanation)
        self.assertEqual(result.data_status, "prototype_illustrative")

    def test_personalized_skill_overlap_and_gaps_follow_profile_and_selected_learning(self) -> None:
        baseline = analyze_career_switch(self.session, self.profile, self.request())
        learned = analyze_career_switch(
            self.session,
            self.profile,
            self.request(learned_skills=["roadmapping", "stakeholder_management", "user_research"]),
        )

        self.assertGreater(baseline.skill_overlap, 0)
        self.assertTrue(any(item.label == "Stakeholder management" for item in baseline.transferable_skills))
        self.assertTrue(baseline.skills_to_develop)
        self.assertLess(len(learned.skills_to_develop), len(baseline.skills_to_develop))
        self.assertTrue(any(item.label == "Roadmapping and prioritization" for item in learned.assumed_skills))
        self.assertGreater(learned.skill_overlap, baseline.skill_overlap)
        self.assertTrue(all(stage.minimum_month <= stage.maximum_month for stage in learned.roadmap))

    def test_difficulty_is_explainable_and_years_reduce_preparation_estimate(self) -> None:
        immediate = analyze_career_switch(self.session, self.profile, self.request())
        after_two = analyze_career_switch(
            self.session,
            self.profile,
            self.request(years_before_switch=2),
        )

        self.assertIn(immediate.transition_difficulty, {"Easy", "Moderate", "Difficult"})
        self.assertEqual(set(immediate.difficulty_factors), {
            "skill_gap", "skill_overlap", "experience_relevance",
            "target_entry_barrier", "market_demand_risk",
        })
        self.assertTrue(immediate.difficulty_explanation)
        self.assertGreater(after_two.experience_relevance_score, immediate.experience_relevance_score)
        self.profile.skills = ["data_analysis"]
        self.profile.interests = ["analytics"]
        self.session.commit()
        fewer_experienced_gaps = analyze_career_switch(self.session, self.profile, self.request())
        more_experienced_gaps = analyze_career_switch(
            self.session, self.profile, self.request(years_before_switch=2)
        )
        self.assertLessEqual(more_experienced_gaps.preparation_min_months, fewer_experienced_gaps.preparation_min_months)
        self.assertNotEqual(immediate.switched_salary[0].role, immediate.stayed_salary[0].role)
        self.assertEqual(after_two.switched_salary[0].role, after_two.stayed_salary[0].role)

    def test_market_and_existing_simulation_salary_curves_are_reused(self) -> None:
        india = analyze_career_switch(self.session, self.profile, self.request())
        usa = analyze_career_switch(
            self.session,
            self.profile,
            self.request(market="US"),
        )

        self.assertEqual(india.market.currency, "INR")
        self.assertEqual(usa.market.currency, "USD")
        self.assertEqual(india.target_market.job_demand, "High")
        self.assertEqual(len(india.stayed_salary), 5)
        self.assertEqual([item.year for item in india.switched_salary], [0, 3, 5, 7, 10])
        self.assertEqual(india.stayed_salary[0].salary_low, 4)
        self.assertEqual(india.switched_salary[0].salary_low, 12)
        self.assertEqual(usa.stayed_salary[0].salary_low, 60000)
        self.assertEqual(usa.switched_salary[0].salary_low, 100000)
        self.assertTrue(all(item.salary_low <= item.salary_mid <= item.salary_high for item in india.switched_salary))

    def test_learning_mba_and_market_what_if_recalculate_analysis(self) -> None:
        baseline = analyze_career_switch(self.session, self.profile, self.request())
        scenario = analyze_career_switch(
            self.session,
            self.profile,
            self.request(
                willing_additional_education=True,
                learned_skills=["product_strategy", "roadmapping", "stakeholder_management"],
                what_if=WhatIfScenario(
                    willing_mba=True,
                    increase_demand=True,
                    increase_ai_adoption=True,
                    increase_salary_growth=True,
                ),
            ),
        )

        self.assertGreater(scenario.skill_overlap, baseline.skill_overlap)
        self.assertEqual(scenario.target_market.demand_index, min(100, baseline.target_market.demand_index + 15))
        self.assertEqual(scenario.target_market.automation_exposure, baseline.target_market.automation_exposure + 15)
        self.assertEqual(scenario.target_market.salary_growth_rate, baseline.target_market.salary_growth_rate + 2)
        self.assertIn("no degree-based salary premium", scenario.education_guidance)
        mba_only = analyze_career_switch(
            self.session,
            self.profile,
            self.request(what_if=WhatIfScenario(willing_mba=True)),
        )
        self.assertGreater(mba_only.preparation_max_months, baseline.preparation_max_months)

    def test_same_career_missing_career_and_unconfigured_transition_errors(self) -> None:
        with self.assertRaises(ValidationError):
            self.request(target_career_id="data-analyst")
        with self.assertRaisesRegex(ValueError, "not in the career database"):
            analyze_career_switch(
                self.session,
                self.profile,
                self.request(target_career_id="missing-career"),
            )
        with self.assertRaisesRegex(ValueError, "No supported transition path"):
            analyze_career_switch(
                self.session,
                self.profile,
                self.request(current_career_id="product-manager", target_career_id="ux-researcher"),
            )

    def test_api_returns_validation_error_for_missing_profile(self) -> None:
        request = self.request(profile_id=999999)
        with self.assertRaises(HTTPException) as error:
            run_career_switch(request, session=self.session, user=self.user)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
