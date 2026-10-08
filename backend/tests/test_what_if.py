import unittest
import math
from datetime import datetime, timezone

from app.data.careers import CAREER_SEED_DATA
from app.data.market_data import CAREER_MARKET_SEED_DATA
from app.models import Career, CareerMarketData, StudentProfile
from app.schemas import WhatIfScenario
from app.services.what_if import compare_what_if
from app.services.simulation import build_career_simulations


class WhatIfComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.careers = [Career(**career) for career in CAREER_SEED_DATA]
        market_rows = [
            CareerMarketData(**row)
            for row in CAREER_MARKET_SEED_DATA
            if row["market_code"] == "IN"
        ]
        self.market_records = {row.career_id: row for row in market_rows}
        self.us_market_records = {
            record.career_id: record
            for record in (
                CareerMarketData(**data)
                for data in CAREER_MARKET_SEED_DATA
                if data["market_code"] == "US"
            )
        }
        self.profile = StudentProfile(
            id=11,
            name="Nyra",
            education_level="undergraduate",
            field_of_study="Economics",
            skills=["data_analysis", "communication"],
            interests=["analytics", "business_strategy"],
            work_preferences=["collaborative"],
            career_priorities=["growth", "impact"],
            created_at=datetime.now(timezone.utc),
        )

    def _profile_with_headroom(self) -> StudentProfile:
        return StudentProfile(
            id=self.profile.id,
            name=self.profile.name,
            education_level=self.profile.education_level,
            field_of_study=self.profile.field_of_study,
            skills=[],
            interests=["technology"],
            work_preferences=["structured"],
            career_priorities=["growth"],
            created_at=self.profile.created_at,
        )

    def test_empty_scenario_preserves_baseline_scores_and_trajectories(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(),
            self.market_records,
        )

        for career in comparison.careers:
            self.assertEqual(career.baseline_score, career.scenario_score)
            self.assertEqual(career.score_change, 0)
            self.assertFalse(career.trajectory_changed)
            self.assertEqual(career.baseline_simulation, career.scenario_simulation)
            self.assertTrue(career.trajectory_explanation)

    def test_avoid_coding_changes_fit_with_per_career_explanations(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(avoid_coding=True),
            self.market_records,
        )
        results = {career.career_id: career for career in comparison.careers}

        self.assertEqual(results["data-analyst"].score_change, -16.0)
        self.assertEqual(results["software-developer"].score_change, -16.0)
        self.assertEqual(results["product-analyst"].score_effects[0].points, 4.0)
        self.assertEqual(results["product-analyst"].score_change, 3.3)
        self.assertFalse(results["data-analyst"].trajectory_changed)
        self.assertTrue(results["data-analyst"].trajectory_explanation)
        self.assertTrue(all(career.score_effects for career in results.values()))

    def test_faster_growth_changes_roles_and_salary_points_without_mutating_baseline(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "US",
            WhatIfScenario(faster_growth=True),
            self.us_market_records,
        )
        product = next(career for career in comparison.careers if career.career_id == "product-analyst")

        self.assertTrue(product.trajectory_changed)
        self.assertEqual(product.baseline_simulation.years[0], product.scenario_simulation.years[0])
        self.assertEqual(
            product.baseline_simulation.years[4].salary_mid,
            product.scenario_simulation.years[3].salary_mid,
        )
        self.assertEqual(product.baseline_simulation.years[4].role, product.scenario_simulation.years[3].role)
        self.assertIn("one year", product.trajectory_explanation)
        self.assertEqual(product.baseline_simulation.years[3].salary_mid, 117500)

    def test_mba_adds_sample_management_route_but_does_not_invent_salary_premium(self) -> None:
        profile = self._profile_with_headroom()
        comparison = compare_what_if(
            profile,
            self.careers,
            "IN",
            WhatIfScenario(willing_mba=True),
            self.market_records,
        )
        product = next(career for career in comparison.careers if career.career_id == "product-analyst")
        analyst = next(career for career in comparison.careers if career.career_id == "data-analyst")

        self.assertEqual(product.score_change, 8.0)
        self.assertIn("Product Director (MBA route)", product.scenario_simulation.years[10].role)
        self.assertEqual(
            product.baseline_simulation.years[10].salary_mid,
            product.scenario_simulation.years[10].salary_mid,
        )
        self.assertFalse(analyst.trajectory_changed)
        self.assertEqual(analyst.score_change, 0.0)

    def test_growth_and_mba_assumptions_compose_in_one_scenario(self) -> None:
        profile = self._profile_with_headroom()
        comparison = compare_what_if(
            profile,
            self.careers,
            "IN",
            WhatIfScenario(willing_mba=True, faster_growth=True),
            self.market_records,
        )
        product = next(career for career in comparison.careers if career.career_id == "product-analyst")

        self.assertEqual(product.score_change, 16.0)
        self.assertEqual(product.scenario_simulation.years[6].role, "Product Manager (MBA route)")
        self.assertIn("one year", product.trajectory_explanation)
        self.assertIn("MBA-oriented", product.trajectory_explanation)

    def test_score_effect_is_reported_when_100_point_cap_hides_the_increase(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(willing_mba=True),
            self.market_records,
        )
        product = next(career for career in comparison.careers if career.career_id == "product-analyst")

        self.assertLess(product.baseline_score, 100.0)
        self.assertEqual(product.score_effects[0].points, 8.0)
        self.assertEqual(product.scenario_score, 100.0)
        self.assertLess(product.score_change, product.score_effects[0].points)

    def test_preferences_only_change_fit_and_scores_remain_bounded(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(
                higher_salary=True,
                work_life_balance=True,
                remote_work=True,
                international_opportunities=True,
            ),
            self.market_records,
        )

        self.assertTrue(all(0 <= career.scenario_score <= 100 for career in comparison.careers))
        self.assertTrue(all(not career.trajectory_changed for career in comparison.careers))
        self.assertTrue(all(career.scenario_simulation == career.baseline_simulation for career in comparison.careers))
        self.assertTrue(all(career.trajectory_explanation for career in comparison.careers))

    def test_market_demand_scenario_updates_fit_and_outlook_without_inventing_salary_change(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(decrease_demand=True),
            self.market_records,
        )
        ux = next(career for career in comparison.careers if career.career_id == "ux-researcher")

        self.assertEqual(ux.baseline_market.demand_index, 54)
        self.assertEqual(ux.scenario_market.demand_index, 39)
        self.assertEqual(ux.scenario_market.job_demand, "Low")
        self.assertLess(ux.score_change, 0)
        self.assertEqual(
            ux.baseline_simulation.years,
            ux.scenario_simulation.years,
        )
        self.assertFalse(ux.trajectory_changed)
        self.assertIn("do not invent", ux.trajectory_explanation)

    def test_ai_adoption_scenario_updates_exposure_and_fit_explanation(self) -> None:
        comparison = compare_what_if(
            self.profile,
            self.careers,
            "US",
            WhatIfScenario(increase_ai_adoption=True),
            self.us_market_records,
        )
        developer = next(career for career in comparison.careers if career.career_id == "software-developer")

        self.assertEqual(developer.baseline_market.automation_exposure, 61)
        self.assertEqual(developer.scenario_market.automation_exposure, 76)
        self.assertEqual(developer.scenario_market.ai_impact, "high")
        self.assertLess(developer.score_change, 0)
        self.assertTrue(any(effect.condition == "increase_ai_adoption" for effect in developer.score_effects))

    def test_salary_growth_scenario_changes_salary_curve_and_skills_importance_changes_market_weight(self) -> None:
        salary_comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(increase_salary_growth=True),
            self.market_records,
        )
        product = next(career for career in salary_comparison.careers if career.career_id == "product-analyst")
        self.assertEqual(product.scenario_market.salary_growth_rate, 10.5)
        self.assertGreater(
            product.scenario_simulation.years[10].salary_mid,
            product.baseline_simulation.years[10].salary_mid,
        )
        self.assertTrue(product.trajectory_changed)

        skills_comparison = compare_what_if(
            self.profile,
            self.careers,
            "IN",
            WhatIfScenario(emerging_skills_important=True),
            self.market_records,
        )
        skills_product = next(career for career in skills_comparison.careers if career.career_id == "product-analyst")
        self.assertEqual(skills_product.baseline_skill_gap, skills_product.scenario_skill_gap)
        self.assertLess(skills_product.scenario_market_score, skills_product.baseline_market_score)
        self.assertTrue(any(effect.condition == "emerging_skills_important" for effect in skills_product.score_effects))

    def test_profile_skill_rating_personalizes_fit_context_without_inventing_salary_effect(self) -> None:
        low_rating_profile = self._profile_with_headroom()
        low_rating_profile.skill_ratings = {"python": 1}
        high_rating_profile = self._profile_with_headroom()
        high_rating_profile.skill_ratings = {"python": 5}

        low = compare_what_if(low_rating_profile, self.careers, "IN", WhatIfScenario(), self.market_records)
        high = compare_what_if(high_rating_profile, self.careers, "IN", WhatIfScenario(), self.market_records)
        low_dev = next(item for item in low.careers if item.career_id == "software-developer")
        high_dev = next(item for item in high.careers if item.career_id == "software-developer")

        self.assertNotEqual(low_dev.scenario_score, high_dev.scenario_score)
        self.assertNotEqual(low_dev.scenario_skill_gap, high_dev.scenario_skill_gap)
        self.assertEqual(low_dev.baseline_simulation.years, high_dev.scenario_simulation.years)

    def test_baseline_simulations_are_finite_for_each_market_and_invalid_career_is_rejected(self) -> None:
        for market_code in ("IN", "US"):
            market, simulations = build_career_simulations(self.careers, market_code)
            self.assertEqual(market.code, market_code)
            self.assertEqual(len(simulations), len(self.careers))
            for simulation in simulations:
                self.assertEqual(len(simulation.years), 11)
                for point in simulation.years:
                    self.assertTrue(all(math.isfinite(value) for value in (
                        point.salary_low, point.salary_mid, point.salary_high,
                    )))

        invalid_career = Career(
            id="unknown-career",
            title="Unknown career",
            category="Test",
            summary="Test fixture",
            relevant_skills=[],
            related_interests=[],
            work_styles=[],
            priorities=[],
            starter_roles=[],
        )
        with self.assertRaisesRegex(RuntimeError, "not configured"):
            build_career_simulations([invalid_career], "IN")


if __name__ == "__main__":
    unittest.main()
