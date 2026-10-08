import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.data.careers import CAREER_SEED_DATA
from app.db.base import Base
from app.models import Career, CareerMarketData, StudentProfile, User
from app.api.routes import demo_market_update
from app.schemas import WhatIfScenario
from app.services.market_service import (
    LocalMarketDataProvider,
    apply_demo_market_update,
    evaluate_market_fit,
    market_catalog,
    market_entry,
    market_intelligence,
    market_records,
    seed_market_data,
    enrich_simulations_with_market,
)
from app.services.career_twin import generate_career_twin
from app.services.simulation import build_career_simulations
from app.services.what_if import compare_what_if


class MarketIntelligenceTests(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_local_provider_returns_labeled_illustrative_market_signals(self) -> None:
        result = market_intelligence(self.session, "IN")

        self.assertEqual(result.provider, "local_illustrative_dataset")
        self.assertEqual(result.market.label, "India")
        self.assertEqual(result.market.currency, "INR")
        self.assertEqual(result.data_status, "prototype_illustrative")
        self.assertIn("synthetic", result.description)
        self.assertEqual(len(result.careers), len(CAREER_SEED_DATA))
        self.assertTrue(all(signal.data_confidence == 0.25 for signal in result.careers))
        self.assertTrue(all("not sourced" in signal.data_source for signal in result.careers))

    def test_market_catalog_is_extensible_but_only_configured_markets_are_enabled(self) -> None:
        catalog = {market.code: market for market in market_catalog()}

        self.assertEqual(set(catalog), {"IN", "US", "UK", "CA", "AU", "DE"})
        self.assertTrue(catalog["IN"].available)
        self.assertTrue(catalog["US"].available)
        self.assertFalse(catalog["UK"].available)
        with self.assertRaisesRegex(ValueError, "not configured"):
            market_entry("UK")

    def test_seed_is_idempotent_and_market_fit_is_bounded_and_explainable(self) -> None:
        seed_market_data(self.session)
        count = self.session.scalar(select(func.count()).select_from(CareerMarketData))
        self.assertEqual(count, len(CAREER_SEED_DATA) * 2)

        record = self.session.scalar(
            select(CareerMarketData).where(
                CareerMarketData.career_id == "product-analyst",
                CareerMarketData.market_code == "IN",
            )
        )
        self.assertIsNotNone(record)
        result = evaluate_market_fit(record, ["data_analysis"])
        self.assertTrue(0 <= result.market_score <= 100)
        self.assertTrue(result.skill_gap)
        self.assertIn("weighted 0–100", result.explanation)

    def test_market_records_include_selected_market_currency_and_salary_units(self) -> None:
        india = market_records(self.session, "IN")
        united_states = market_records(self.session, "US")

        self.assertEqual(india["product-analyst"].currency, "INR")
        self.assertEqual(united_states["product-analyst"].currency, "USD")
        self.assertLess(india["product-analyst"].salary_low, india["product-analyst"].salary_high)
        self.assertLess(
            united_states["product-analyst"].salary_low,
            united_states["product-analyst"].salary_high,
        )
        self.assertNotEqual(
            india["product-analyst"].salary_high,
            united_states["product-analyst"].salary_high,
        )

    def test_provider_persists_demo_refresh_with_provenance_and_new_timestamp(self) -> None:
        provider = LocalMarketDataProvider()
        original = provider.get_for_career(self.session, "IN", "product-analyst")
        self.assertIsNotNone(original)
        original_updated_at = original.last_updated

        before, updated, updated_at = apply_demo_market_update(
            self.session, "IN", "product-analyst"
        )
        self.session.commit()
        persisted = provider.get_for_career(self.session, "IN", "product-analyst")

        self.assertEqual(before.job_demand, "High")
        self.assertEqual(updated.job_demand, "Medium")
        self.assertEqual(updated.demand_index, 50)
        self.assertEqual(updated.demand_trend, "declining")
        self.assertEqual(updated.hiring_trend, "declining")
        self.assertEqual(updated.currency, "INR")
        self.assertEqual(updated.data_status, "prototype_illustrative")
        self.assertIn("no external source", updated.data_source)
        self.assertEqual(updated.data_confidence, 0.25)
        if original_updated_at.tzinfo is None:
            original_updated_at = original_updated_at.replace(tzinfo=timezone.utc)
        self.assertGreater(updated_at, original_updated_at)
        self.assertEqual(persisted.last_updated, updated_at)

    def test_provider_market_refresh_updates_selected_records_without_touching_other_markets(self) -> None:
        provider = LocalMarketDataProvider()
        current = provider.get_for_career(self.session, "IN", "product-analyst")
        self.assertIsNotNone(current)
        candidate = CareerMarketData(**{
            column.name: getattr(current, column.name)
            for column in CareerMarketData.__table__.columns
            if column.name != "id"
        })
        candidate.salary_growth_rate = 9.0
        candidate.data_source = "Reviewed demo fixture"
        original_updated_at = current.last_updated

        refreshed = provider.refresh_market(self.session, "IN", [candidate])
        self.session.commit()
        updated_record = provider.get_for_career(self.session, "IN", "product-analyst")

        self.assertEqual(len(refreshed), len(CAREER_SEED_DATA))
        self.assertEqual(
            updated_record.salary_growth_rate,
            9.0,
        )
        original_utc = (
            original_updated_at.replace(tzinfo=timezone.utc)
            if original_updated_at.tzinfo is None
            else original_updated_at.astimezone(timezone.utc)
        )
        self.assertGreater(updated_record.last_updated.replace(tzinfo=timezone.utc), original_utc)
        self.assertEqual(
            provider.get_for_career(self.session, "US", "product-analyst").salary_growth_rate,
            5.7,
        )

    def test_refresh_endpoint_recalculates_fit_rank_and_explains_before_after(self) -> None:
        profile = StudentProfile(
            user_id=self.user.id,
            name="Nyra",
            education_level="undergraduate",
            field_of_study="Economics",
            skills=["data_analysis", "communication"],
            interests=["analytics", "business_strategy"],
            work_preferences=["collaborative"],
            career_priorities=["growth", "impact"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(profile)
        self.session.commit()

        result = demo_market_update(
            profile.id, "IN", career_id="product-analyst", action="apply", session=self.session, user=self.user
        )

        self.assertEqual(result.before_demand, "High")
        self.assertEqual(result.after_demand, "Medium")
        self.assertLess(result.after_fit_score, result.before_fit_score)
        self.assertGreaterEqual(result.before_rank, 1)
        self.assertGreaterEqual(result.after_rank, 1)
        self.assertIn("demand index", result.explanation)
        self.assertIn("declining", result.explanation)
        self.assertEqual(result.career_twin.market_last_updated.replace(tzinfo=timezone.utc), result.updated_at)
        self.assertEqual(
            result.career_twin.career_options[0].fit_score,
            max(career.fit_score for career in result.career_twin.career_options),
        )
        live_records = market_records(self.session, "IN")
        what_if = compare_what_if(
            profile,
            list(self.session.scalars(select(Career)).all()),
            "IN",
            WhatIfScenario(decrease_demand=True),
            live_records,
        )
        product_scenario = next(
            career for career in what_if.careers if career.career_id == "product-analyst"
        )
        self.assertEqual(product_scenario.baseline_market.job_demand, "Medium")
        self.assertEqual(product_scenario.scenario_market.job_demand, "Low")

        careers = list(self.session.scalars(select(Career)).all())
        _, simulations = build_career_simulations(careers, "IN")
        simulation = next(
            career for career in enrich_simulations_with_market(simulations, live_records)
            if career.career_id == "product-analyst"
        )
        self.assertEqual(simulation.market_outlook.job_demand, "Medium")
        self.assertTrue(all(stage.job_demand == "Medium" for stage in simulation.stages))
        reset = demo_market_update(
            profile.id, "IN", career_id="product-analyst", action="reset", session=self.session, user=self.user
        )
        self.assertEqual(reset.action, "reset")
        self.assertEqual(reset.before_demand, "Medium")
        self.assertEqual(reset.after_demand, "High")
        self.assertGreater(reset.after_fit_score, reset.before_fit_score)

    def test_market_record_change_reorders_fit_ranking(self) -> None:
        profile = StudentProfile(
            name="Nyra",
            education_level="undergraduate",
            field_of_study="Exploration",
            skills=[],
            interests=["analytics"],
            work_preferences=["collaborative"],
            career_priorities=["growth"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(profile)
        self.session.commit()
        for career in self.session.scalars(select(Career)).all():
            career.related_interests = []
            career.relevant_skills = []
            career.work_styles = []
            career.priorities = []
        self.session.commit()
        before = generate_career_twin(self.session, profile, "IN")
        previous_top_id = before.career_options[0].id
        record = market_records(self.session, "IN")[previous_top_id]
        record.demand_index = 0
        record.job_demand = "Low"
        record.demand_trend = "declining"
        record.hiring_trend = "declining"
        record.salary_growth_rate = -5
        record.automation_exposure = 100
        provider = LocalMarketDataProvider()
        provider.update_record(self.session, record)
        self.session.commit()

        after = generate_career_twin(self.session, profile, "IN")

        self.assertNotEqual(after.career_options[0].id, previous_top_id)
        self.assertEqual(
            [career.fit_score for career in after.career_options],
            sorted((career.fit_score for career in after.career_options), reverse=True),
        )


if __name__ == "__main__":
    unittest.main()
