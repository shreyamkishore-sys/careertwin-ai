import unittest

from app.data.career_simulations import CAREER_SIMULATION_DATA, SIMULATION_MARKETS
from app.data.careers import CAREER_SEED_DATA
from app.models import Career
from app.services.simulation import build_career_simulations


class CareerSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.careers = [Career(**career) for career in CAREER_SEED_DATA]

    def test_builds_eleven_annual_points_for_each_market_and_career(self) -> None:
        for market_code, market_data in SIMULATION_MARKETS.items():
            with self.subTest(market=market_code):
                market, simulations = build_career_simulations(self.careers, market_code)

                self.assertEqual(market.code, market_code)
                self.assertEqual(market.currency, market_data["currency"])
                self.assertEqual(
                    {item.career_id for item in simulations},
                    set(CAREER_SIMULATION_DATA),
                )
                for career in simulations:
                    self.assertEqual([point.year for point in career.years], list(range(11)))
                    self.assertEqual(len(career.stages), 5)
                    self.assertEqual(career.stages[0].year, 0)
                    self.assertEqual(career.stages[-1].year, 10)
                    self.assertTrue(all(stage.role and stage.skills for stage in career.stages))
                    self.assertTrue(
                        all(
                            point.salary_low <= point.salary_mid <= point.salary_high
                            for point in career.years
                        )
                    )
                    self.assertTrue(
                        all(
                            earlier.salary_mid <= later.salary_mid
                            for earlier, later in zip(career.years, career.years[1:])
                        )
                    )

    def test_india_and_us_salary_units_are_distinct(self) -> None:
        india, _ = build_career_simulations(self.careers, "IN")
        united_states, _ = build_career_simulations(self.careers, "US")

        self.assertEqual(india.unit, "₹ lakh / year")
        self.assertEqual(united_states.unit, "USD / year")
        self.assertEqual(india.locale, "en-IN")
        self.assertEqual(united_states.locale, "en-US")

    def test_salary_values_are_sampled_in_expected_market_scale(self) -> None:
        _, india_careers = build_career_simulations(self.careers, "IN")
        _, united_states_careers = build_career_simulations(self.careers, "US")
        india_product = next(item for item in india_careers if item.career_id == "product-analyst")
        us_product = next(item for item in united_states_careers if item.career_id == "product-analyst")

        self.assertEqual((india_product.years[0].salary_low, india_product.years[0].salary_high), (6.0, 10.0))
        self.assertEqual((us_product.years[0].salary_low, us_product.years[0].salary_high), (70000.0, 105000.0))

    def test_missing_career_salary_data_is_reported_explicitly(self) -> None:
        unknown_career = Career(
            id="new-career",
            title="New Career",
            category="Other",
            summary="A career missing illustrative data.",
            related_interests=[],
            relevant_skills=[],
            work_styles=[],
            priorities=[],
            starter_roles=["Associate"],
        )

        with self.assertRaisesRegex(RuntimeError, "not configured for: new-career"):
            build_career_simulations([unknown_career], "IN")


if __name__ == "__main__":
    unittest.main()
