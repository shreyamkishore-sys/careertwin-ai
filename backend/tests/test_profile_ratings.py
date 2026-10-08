import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.careers import CAREER_SEED_DATA
from app.data.ai_risk import AI_RISK_DATA
from app.data.career_transitions import TRANSITION_SKILLS
from app.db.base import Base
from app.models import Career, StudentProfile
from app.schemas import StudentProfileInput, StudentProfileRead
from app.services.career_twin import _factor_contributions
from app.services.career_switch import _skill_evidence
from app.services.ai_risk import _readiness
from app.services.profile_ratings import SKILL_KEYS
from app.db import database as database_module


class ProfileRatingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.session.add_all(Career(**career) for career in CAREER_SEED_DATA)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def profile_input(self, **overrides):
        data = {
            "name": "Nyra", "education_level": "undergraduate", "field_of_study": "Economics",
            "skills": ["spreadsheets", "communication", "data_analysis"],
            "interests": ["analytics", "business_strategy"], "work_preferences": ["collaborative", "remote_ready"],
            "career_priorities": ["salary", "growth", "remote_work"],
        }
        data.update(overrides)
        return StudentProfileInput.model_validate(data)

    def test_legacy_profiles_receive_neutral_rating_defaults_without_losing_tags(self):
        profile = self.profile_input()
        self.assertEqual(profile.skills, ["spreadsheets", "communication", "data_analysis"])
        self.assertEqual(profile.skill_ratings["excel"], 4)
        self.assertEqual(profile.skill_ratings["python"], 3)
        self.assertEqual(profile.priority_ratings["salary"], 4)
        self.assertEqual(profile.preference_ratings["remote_work"], 4)

    def test_explicit_rating_maps_accept_nested_camel_case_and_legacy_labels(self):
        profile = self.profile_input(
            skill_ratings={"businessKnowledge": 4, "aiLiteracy": 2},
            priority_ratings={"careerGrowth": 5, "lowCoding": 5},
            preference_ratings={"coding": "Low", "analytical": "High", "remoteWork": 5},
        )
        self.assertEqual(profile.skill_ratings["business_knowledge"], 4)
        self.assertEqual(profile.skill_ratings["ai_literacy"], 2)
        self.assertEqual(profile.priority_ratings["career_growth"], 5)
        self.assertEqual(profile.preference_ratings["coding"], 1)
        self.assertEqual(profile.preference_ratings["analytical_work"], 4)

    def test_legacy_preference_and_priority_lists_map_to_numeric_values(self):
        profile = self.profile_input(
            work_preferences=[], career_priorities=[],
            preferences=["Analytical", "Remote", "Coding: Low"],
            priorities=["Salary", "Career Growth", "Low Coding"],
        )
        self.assertIn("independent", profile.work_preferences)
        self.assertIn("remote_ready", profile.work_preferences)
        self.assertEqual(profile.preference_ratings["analytical_work"], 4)
        self.assertEqual(profile.preference_ratings["coding"], 1)
        self.assertEqual(profile.priority_ratings["salary"], 4)
        self.assertEqual(profile.priority_ratings["career_growth"], 4)

    def test_invalid_explicit_ratings_are_rejected(self):
        with self.assertRaises(ValueError):
            self.profile_input(skill_ratings={"sql": 6})
        with self.assertRaises(ValueError):
            self.profile_input(priority_ratings={"salary": "NaN"})

    def test_old_database_profile_serializes_with_safe_rating_defaults(self):
        profile = StudentProfile(
            id=123,
            name="Legacy", education_level="undergraduate", field_of_study="Economics",
            skills=["spreadsheets"], interests=["analytics"], work_preferences=["remote_ready"],
            career_priorities=["growth"], skill_ratings=None, preference_ratings=None,
            priority_ratings=None, created_at=datetime.now(timezone.utc),
        )
        read = StudentProfileRead.model_validate(profile)
        self.assertEqual(read.skill_ratings["excel"], 4)
        self.assertEqual(read.preference_ratings["coding"], 3)
        self.assertEqual(read.priority_ratings["salary"], 3)

    def test_skill_proficiency_changes_career_fit_contribution(self):
        career = self.session.get(Career, "data-analyst")
        low = StudentProfile(
            name="Low", education_level="undergraduate", field_of_study="Economics", skills=[],
            interests=["analytics"], work_preferences=["independent"], career_priorities=["growth"],
            skill_ratings={key: 1 for key in SKILL_KEYS}, preference_ratings={"coding": 3},
            priority_ratings={"salary": 3}, created_at=datetime.now(timezone.utc),
        )
        high = StudentProfile(
            name="High", education_level="undergraduate", field_of_study="Economics", skills=[],
            interests=["analytics"], work_preferences=["independent"], career_priorities=["growth"],
            skill_ratings={key: 5 for key in SKILL_KEYS}, preference_ratings={"coding": 3},
            priority_ratings={"salary": 3}, created_at=datetime.now(timezone.utc),
        )
        low_points = next(item.points for item in _factor_contributions(low, career) if item.factor == "skills")
        high_points = next(item.points for item in _factor_contributions(high, career) if item.factor == "skills")
        self.assertGreater(high_points, low_points)

    def test_ai_readiness_uses_ai_literacy_level_and_exposes_gap(self):
        values = {key: 3 for key in SKILL_KEYS}
        values["ai_literacy"] = 2
        low = StudentProfile(
            name="Nyra", education_level="undergraduate", field_of_study="Economics", skills=[],
            interests=["analytics"], work_preferences=["remote_ready"], career_priorities=["growth"],
            skill_ratings=dict(values), preference_ratings={}, priority_ratings={}, created_at=datetime.now(timezone.utc),
        )
        values["ai_literacy"] = 5
        high = StudentProfile(
            name="Nyra", education_level="undergraduate", field_of_study="Economics", skills=[],
            interests=["analytics"], work_preferences=["remote_ready"], career_priorities=["growth"],
            skill_ratings=dict(values), preference_ratings={}, priority_ratings={}, created_at=datetime.now(timezone.utc),
        )
        low_readiness = _readiness(AI_RISK_DATA["data-analyst"], low, False, False)
        high_readiness = _readiness(AI_RISK_DATA["data-analyst"], high, False, False)
        self.assertLess(low_readiness.baseline_score, high_readiness.baseline_score)
        ai_literacy = next(item for item in low_readiness.skill_evidence if item.label == "AI literacy")
        self.assertEqual((ai_literacy.current_rating, ai_literacy.required_rating, ai_literacy.gap), (2, 4, 2))

    def test_career_switch_skill_evidence_reflects_numeric_proficiency_gap(self):
        values = {key: 3 for key in SKILL_KEYS}
        values["sql"] = 3
        profile = StudentProfile(
            name="Nyra", education_level="undergraduate", field_of_study="Economics", skills=["data_analysis"],
            interests=["analytics"], work_preferences=["remote_ready"], career_priorities=["growth"],
            skill_ratings=values, preference_ratings={}, priority_ratings={}, created_at=datetime.now(timezone.utc),
        )
        current = self.session.get(Career, "business-analyst")
        requirement = next(item for item in TRANSITION_SKILLS["data-analyst"]["requirements"] if item["label"] == "SQL / data tools")
        result = _skill_evidence(requirement, profile, current, [])
        self.assertEqual(result.status, "partially_transferable")
        self.assertEqual((result.current_rating, result.required_rating, result.gap), (3, 4, 1))

    def test_database_startup_adds_rating_columns_to_existing_profile_table(self):
        legacy_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        with legacy_engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE student_profiles (id INTEGER PRIMARY KEY, name VARCHAR(60) NOT NULL, "
                "education_level VARCHAR(40) NOT NULL, field_of_study VARCHAR(120) NOT NULL, "
                "skills JSON NOT NULL, interests JSON NOT NULL, work_preferences JSON NOT NULL, "
                "career_priorities JSON NOT NULL, created_at DATETIME NOT NULL)"
            ))
        with patch.object(database_module, "engine", legacy_engine), patch.object(
            database_module, "SessionLocal", sessionmaker(bind=legacy_engine, autoflush=False, expire_on_commit=False)
        ):
            database_module.create_database()
        columns = {item["name"] for item in inspect(legacy_engine).get_columns("student_profiles")}
        self.assertTrue({"skill_ratings", "priority_ratings", "preference_ratings"}.issubset(columns))
        legacy_engine.dispose()


if __name__ == "__main__":
    unittest.main()
