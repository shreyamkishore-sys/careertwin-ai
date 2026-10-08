import unittest
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import get_ai_risk_catalog, run_ai_risk_analysis
from app.data.ai_risk import AI_RISK_DATA
from app.data.careers import CAREER_SEED_DATA
from app.db.base import Base
from app.models import Career, StudentProfile, User
from app.schemas import AIRiskAnalysisInput, WhatIfScenario
from app.services.ai_risk import analyze_ai_risk
from app.services.market_service import apply_demo_market_update, seed_market_data


class AIRiskTests(unittest.TestCase):
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
            interests=["analytics", "business_strategy"],
            work_preferences=["collaborative", "structured"],
            career_priorities=["growth", "impact"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(self.profile)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def request(self, **overrides: object) -> AIRiskAnalysisInput:
        values: dict[str, object] = {
            "profile_id": self.profile.id,
            "market": "IN",
            "what_if": WhatIfScenario(),
        }
        values.update(overrides)
        return AIRiskAnalysisInput(**values)

    def test_catalog_returns_configured_careers_with_market_provenance(self) -> None:
        result = get_ai_risk_catalog(market="IN", session=self.session)
        by_id = {career.career_id: career for career in result.careers}

        self.assertEqual(set(by_id), set(AI_RISK_DATA))
        self.assertIn("digital-marketing-manager", by_id)
        self.assertIn("hr-analyst", by_id)
        self.assertEqual(result.data_status, "prototype_illustrative")
        self.assertIn("not sourced", by_id["product-analyst"].data_source)
        self.assertEqual(by_id["data-analyst"].ai_impact_score, 68)
        self.assertEqual(by_id["product-manager"].ai_impact_score, 38)

    def test_analysis_uses_profile_tags_without_fabricating_skill_levels(self) -> None:
        result = analyze_ai_risk(
            self.session,
            "product-analyst",
            self.profile,
            self.request(),
        )
        readiness_skills = {skill.label: skill.status for skill in result.readiness.skill_evidence}

        self.assertEqual(result.baseline.ai_impact_score, 55)
        self.assertEqual(result.baseline.automation_exposure, 45)
        self.assertIn("Communication", result.readiness.strengths)
        self.assertEqual(readiness_skills["AI literacy"], "gap")
        self.assertNotIn("4/5", result.readiness.explanation)
        self.assertEqual(result.baseline_market.market.currency, "INR")
        self.assertEqual(result.baseline_market.data_status, "prototype_illustrative")
        self.assertTrue(result.tasks)
        self.assertTrue(result.assumptions)

    def test_existing_what_if_settings_recalculate_ai_readiness_and_task_exposure(self) -> None:
        sparse_profile = StudentProfile(
            name="Sparse Profile",
            education_level="undergraduate",
            field_of_study="General Studies",
            skills=[],
            interests=["analytics"],
            work_preferences=["independent"],
            career_priorities=["growth"],
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(sparse_profile)
        self.session.commit()
        baseline = analyze_ai_risk(
            self.session, "data-analyst", sparse_profile,
            AIRiskAnalysisInput(profile_id=sparse_profile.id),
        )
        scenario = analyze_ai_risk(
            self.session,
            "data-analyst",
            sparse_profile,
            AIRiskAnalysisInput(
                profile_id=sparse_profile.id,
                what_if=WhatIfScenario(
                    learn_technical_skills=True,
                    increase_ai_adoption=True,
                    emerging_skills_important=True,
                ),
            ),
        )

        self.assertEqual(scenario.scenario.ai_impact_score, min(100, baseline.baseline.ai_impact_score + 15))
        self.assertEqual(scenario.scenario.automation_exposure, baseline.baseline.automation_exposure + 15)
        self.assertGreater(scenario.readiness.scenario_score, baseline.readiness.scenario_score)
        self.assertGreater(scenario.scenario_market.automation_exposure, scenario.baseline_market.automation_exposure)
        self.assertTrue(scenario.readiness.assumed_skills)
        self.assertEqual(len(scenario.scenario_effects), 3)

    def test_task_categories_and_resilience_are_deterministic(self) -> None:
        first = analyze_ai_risk(
            self.session, "business-analyst", self.profile, self.request()
        )
        second = analyze_ai_risk(
            self.session, "business-analyst", self.profile, self.request()
        )

        self.assertEqual(first.baseline.ai_resilience_score, second.baseline.ai_resilience_score)
        self.assertEqual(
            [(task.name, task.category) for task in first.tasks],
            [(task.name, task.category) for task in second.tasks],
        )
        self.assertIn("highly_automatable", {task.category for task in first.tasks})
        self.assertIn("human_centric", {task.category for task in first.tasks})

    def test_analysis_reflects_market_refresh_provenance(self) -> None:
        _, updated, updated_at = apply_demo_market_update(
            self.session, "IN", "product-analyst"
        )
        self.session.commit()
        result = analyze_ai_risk(
            self.session, "product-analyst", self.profile, self.request()
        )

        self.assertEqual(result.scenario_market.job_demand, updated.job_demand)
        self.assertEqual(result.scenario_market.last_updated, updated_at)
        self.assertEqual(result.scenario_market.data_status, "prototype_illustrative")

    def test_unknown_career_and_missing_profile_return_validation_errors(self) -> None:
        with self.assertRaises(HTTPException) as unknown:
            run_ai_risk_analysis(
                "unknown-career",
                self.request(),
                session=self.session,
                user=self.user,
            )
        self.assertEqual(unknown.exception.status_code, 422)

        with self.assertRaises(HTTPException) as missing:
            run_ai_risk_analysis(
                "product-analyst",
                AIRiskAnalysisInput(profile_id=9999),
                session=self.session,
                user=self.user,
            )
        self.assertEqual(missing.exception.status_code, 404)
