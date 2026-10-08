import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.data.careers import CAREER_SEED_DATA
from app.services.market_service import seed_market_data
from app.db.base import Base
from app.models import Career, CareerMarketData, CareerTwin, StudentProfile
from app.services.career_twin import generate_career_twin


class CareerTwinGenerationTests(unittest.TestCase):
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
        self.profile = StudentProfile(
            name="Nyra",
            education_level="undergraduate",
            field_of_study="Economics",
            skills=["data_analysis", "communication"],
            interests=["analytics", "business_strategy"],
            work_preferences=["collaborative"],
            career_priorities=["growth", "impact"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(self.profile)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_generation_personalizes_reasons_and_persists_one_twin(self) -> None:
        twin = generate_career_twin(self.session, self.profile)

        self.assertEqual(len(twin.career_options), len(CAREER_SEED_DATA))
        self.assertEqual(len(twin.recommended_careers), 3)
        self.assertEqual(twin.profile.name, "Nyra")
        self.assertIn(
            "Builds on your data analysis skill",
            next(career for career in twin.career_options if career.id == "data-analyst").match_reasons,
        )
        self.assertTrue(all(career.match_reasons for career in twin.recommended_careers))
        self.assertIn("not probabilities", twin.overview.lower())
        product_analyst = next(
            career for career in twin.career_options if career.id == "product-analyst"
        )
        self.assertEqual(product_analyst.profile_fit_score, 100.0)
        self.assertEqual(product_analyst.fit_score, round(
            product_analyst.profile_fit_score * 0.85
            + product_analyst.market_fit_score * 0.15,
            1,
        ))
        self.assertEqual(
            [item.points for item in product_analyst.factor_contributions],
            [40.0, 30.0, 15.0, 15.0],
        )
        self.assertEqual(
            len(list(self.session.scalars(select(CareerTwin)).all())),
            1,
        )

    def test_regeneration_refreshes_the_existing_twin(self) -> None:
        first = generate_career_twin(self.session, self.profile)
        self.profile.interests = ["design_creativity", "research"]
        self.profile.skills = ["visual_design", "research"]
        self.session.commit()

        refreshed = generate_career_twin(self.session, self.profile)

        self.assertEqual(first.id, refreshed.id)
        self.assertEqual(refreshed.profile.interests, ["design_creativity", "research"])
        self.assertEqual(refreshed.recommended_careers[0].id, "ux-researcher")
        self.assertEqual(
            len(list(self.session.scalars(select(CareerTwin)).all())),
            1,
        )

    def test_seed_dataset_contains_careers_without_external_services(self) -> None:
        self.assertEqual(len(list(self.session.scalars(select(Career)).all())), len(CAREER_SEED_DATA))

    def test_career_twin_exposes_all_skill_requirements_with_profile_ratings(self) -> None:
        self.profile.skill_ratings = {"sql": 2, "python": 5}
        self.session.commit()

        twin = generate_career_twin(self.session, self.profile)
        analyst = next(item for item in twin.career_options if item.id == "data-analyst")
        requirements = {item.skill_key: item for item in analyst.skill_requirements}

        self.assertEqual(requirements["sql"].current_rating, 2)
        self.assertEqual(requirements["sql"].required_rating, 4)
        self.assertEqual(requirements["python"].current_rating, 5)
        self.assertEqual(requirements["python"].required_rating, 3)
        self.assertTrue(any(gap.skill == "Sql" and gap.current_rating == 2 for gap in analyst.skill_gaps))
        development_sql = next(item for item in analyst.development_plan.items if item.skill_key == "sql")
        self.assertEqual((development_sql.current_rating, development_sql.required_rating, development_sql.gap), (2, 4, 2))

    def test_each_factor_explains_matches_and_unmatched_selections(self) -> None:
        career = next(
            career for career in self.session.scalars(select(Career)).all()
            if career.id == "data-analyst"
        )

        twin = generate_career_twin(self.session, self.profile)
        result = next(item for item in twin.career_options if item.id == career.id)
        factors = {item.factor: item for item in result.factor_contributions}

        self.assertEqual(
            [(item.factor, item.weight) for item in result.factor_contributions],
            [
                ("interests", 40.0),
                ("skills", 30.0),
                ("work_preferences", 15.0),
                ("career_priorities", 15.0),
            ],
        )
        self.assertEqual(factors["interests"].points, 20.0)
        self.assertEqual(factors["interests"].matched_items, ["analytical problem-solving"])
        self.assertEqual(factors["interests"].unmatched_items, ["business strategy"])
        self.assertEqual(factors["skills"].points, 15.0)
        self.assertEqual(factors["work_preferences"].points, 0.0)
        self.assertIn(
            "0 of 1 selected work preferences",
            factors["work_preferences"].explanation,
        )
        self.assertEqual(
            result.profile_fit_score,
            sum(factor.points for factor in result.factor_contributions),
        )

    def test_scores_are_bounded_and_ordered_by_score(self) -> None:
        twin = generate_career_twin(self.session, self.profile)
        scores = [career.fit_score for career in twin.career_options]

        self.assertTrue(all(0 <= score <= 100 for score in scores))
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(twin.recommended_careers, twin.career_options[:3])

    def test_unselected_skills_do_not_penalize_fit(self) -> None:
        self.profile.skills = []
        self.session.commit()

        twin = generate_career_twin(self.session, self.profile)
        data_analyst = next(
            career for career in twin.career_options if career.id == "data-analyst"
        )
        skill_factor = next(
            factor
            for factor in data_analyst.factor_contributions
            if factor.factor == "skills"
        )

        self.assertEqual(skill_factor.points, 0.0)
        self.assertEqual(skill_factor.selected_count, 0)
        self.assertFalse(skill_factor.unmatched_items)

    def test_market_updates_recalculate_career_scores_deterministically(self) -> None:
        before = generate_career_twin(self.session, self.profile, "IN")
        before_product = next(
            career for career in before.career_options if career.id == "product-analyst"
        )
        signal = self.session.scalar(
            select(CareerMarketData).where(
                CareerMarketData.career_id == "product-analyst",
                CareerMarketData.market_code == "IN",
            )
        )
        self.assertIsNotNone(signal)
        signal.demand_index = 50
        signal.job_demand = "Medium"
        self.session.commit()

        after = generate_career_twin(self.session, self.profile, "IN")
        after_product = next(
            career for career in after.career_options if career.id == "product-analyst"
        )

        self.assertEqual(before.id, after.id)
        self.assertEqual(before_product.profile_fit_score, after_product.profile_fit_score)
        self.assertEqual(after_product.market_outlook.job_demand, "Medium")
        self.assertLess(after_product.fit_score, before_product.fit_score)
        self.assertEqual(
            after_product.fit_score,
            round(
                after_product.profile_fit_score * 0.85
                + after_product.market_fit_score * 0.15,
                1,
            ),
        )


if __name__ == "__main__":
    unittest.main()
