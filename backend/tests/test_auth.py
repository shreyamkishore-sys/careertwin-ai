import unittest
import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from pydantic import ValidationError
from starlette.requests import Request

from app.api.auth_routes import log_in, log_out, me, sign_up
from app.api.routes import create_career_twin, create_profile, get_profile
from app.main import app
from app.data.careers import CAREER_SEED_DATA
from app.db.base import Base
from app.db import database as database_module
from app.models import AuthSession, Career, StudentProfile, User
from app.schemas import LoginInput, SignUpInput, StudentProfileInput
from app.services.auth import (
    SESSION_COOKIE,
    create_session,
    current_user_dependency,
    current_user_for_token,
    hash_password,
    verify_password,
)
from app.services.market_service import seed_market_data


def request_with_cookie(token: str | None = None) -> Request:
    headers = [] if token is None else [(b"cookie", f"{SESSION_COOKIE}={token}".encode())]
    return Request({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "GET", "scheme": "http", "path": "/api/auth/me",
        "raw_path": b"/api/auth/me", "query_string": b"", "headers": headers,
        "server": ("testserver", 80), "client": ("testclient", 50000), "root_path": "",
    })


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.session.add_all(Career(**career) for career in CAREER_SEED_DATA)
        self.session.commit()
        seed_market_data(self.session)
        def override_get_db():
            with Session(self.engine, expire_on_commit=False) as request_session:
                yield request_session
        app.dependency_overrides[database_module.get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.session.close()
        self.engine.dispose()

    def http_request(self, method, path, body=None, cookie=None):
        raw_body = json.dumps(body).encode() if body is not None else b""
        headers = []
        if body is not None:
            headers.append((b"content-type", b"application/json"))
        if cookie:
            headers.append((b"cookie", cookie.encode()))
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": path.split("?", 1)[0],
            "raw_path": path.split("?", 1)[0].encode(),
            "query_string": path.split("?", 1)[1].encode() if "?" in path else b"",
            "headers": headers, "server": ("testserver", 80),
            "client": ("testclient", 50000), "root_path": "",
        }
        received = False
        messages = []

        async def receive():
            nonlocal received
            if received:
                return {"type": "http.disconnect"}
            received = True
            return {"type": "http.request", "body": raw_body, "more_body": False}

        async def send(message):
            messages.append(message)

        asyncio.run(app(scope, receive, send))
        status_code = next(item["status"] for item in messages if item["type"] == "http.response.start")
        response_headers = dict(next(item["headers"] for item in messages if item["type"] == "http.response.start"))
        response_body = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
        return status_code, response_headers, json.loads(response_body) if response_body else None

    def signup_data(self, **overrides):
        values = {"name": "Nyra Shah", "email": "nyra@example.com", "password": "CareerTwin!2026"}
        values.update(overrides)
        return SignUpInput.model_validate(values)

    def profile_data(self):
        return StudentProfileInput.model_validate({
            "name": "Nyra Shah", "education_level": "undergraduate", "field_of_study": "Economics",
            "skills": ["data_analysis", "communication"], "skill_ratings": {"data_analysis": 2},
            "interests": ["analytics", "business_strategy"], "work_preferences": ["collaborative"],
            "career_priorities": ["growth", "impact"], "priority_ratings": {"career_growth": 5},
        })

    def test_successful_signup_hashes_password_and_returns_safe_account(self):
        response = Response()
        result = sign_up(self.signup_data(), response, self.session)
        user = self.session.get(User, result.id)
        self.assertEqual(result.email, "nyra@example.com")
        self.assertIsNone(result.profile_id)
        self.assertFalse(hasattr(result, "password"))
        self.assertFalse(hasattr(result, "password_hash"))
        self.assertNotEqual(user.password_hash, "CareerTwin!2026")
        self.assertTrue(verify_password("CareerTwin!2026", user.password_hash))
        self.assertIn("httponly", response.headers["set-cookie"].lower())
        self.assertEqual(len(list(self.session.scalars(select(User)).all())), 1)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        sign_up(self.signup_data(), Response(), self.session)
        with self.assertRaises(HTTPException) as error:
            sign_up(self.signup_data(email="NYRA@example.com"), Response(), self.session)
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(error.exception.detail, "An account with this email already exists.")

    def test_invalid_signup_input_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.signup_data(email="not-an-email")
        with self.assertRaises(ValidationError):
            self.signup_data(password="short")
        with self.assertRaises(ValidationError):
            self.signup_data(name=" ")

    def test_login_and_authenticated_user_retrieval(self):
        registered = sign_up(self.signup_data(), Response(), self.session)
        response = Response()
        logged_in = log_in(LoginInput(email="NYRA@example.com", password="CareerTwin!2026"), response, self.session)
        token = response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]
        self.assertEqual(logged_in.id, registered.id)
        current_user = current_user_dependency(request_with_cookie(token), self.session)
        self.assertEqual(me(current_user, self.session).email, "nyra@example.com")
        self.assertIs(current_user_for_token(self.session, token), self.session.get(User, registered.id))

    def test_invalid_login_uses_generic_error(self):
        sign_up(self.signup_data(), Response(), self.session)
        with self.assertRaises(HTTPException) as error:
            log_in(LoginInput(email="unknown@example.com", password="wrong-password"), Response(), self.session)
        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail, "Invalid email or password.")
        with self.assertRaises(HTTPException) as error:
            log_in(LoginInput(email="nyra@example.com", password="wrong-password"), Response(), self.session)
        self.assertEqual(error.exception.detail, "Invalid email or password.")

    def test_expired_session_is_rejected(self):
        user = User(name="Nyra", email="nyra@example.com", password_hash=hash_password("CareerTwin!2026"), created_at=datetime.now(timezone.utc))
        self.session.add(user)
        self.session.commit()
        token = "expired-test-token"
        self.session.add(AuthSession(
            user_id=user.id, token_hash=__import__("hashlib").sha256(token.encode()).hexdigest(),
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        ))
        self.session.commit()
        self.assertIsNone(current_user_for_token(self.session, token))

    def test_logout_revokes_session_and_clears_cookie(self):
        user = User(name="Nyra", email="nyra@example.com", password_hash=hash_password("CareerTwin!2026"), created_at=datetime.now(timezone.utc))
        self.session.add(user)
        self.session.commit()
        token = create_session(self.session, user)
        response = Response()
        logged_out = log_out(request_with_cookie(token), response, self.session)
        self.assertEqual(logged_out.status_code, 204)
        self.assertIsNone(current_user_for_token(self.session, token))
        self.assertIn("max-age=0", response.headers["set-cookie"].lower())

    def test_unauthenticated_user_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            current_user_dependency(request_with_cookie(), self.session)
        self.assertEqual(error.exception.status_code, 401)

    def test_profile_is_bound_to_account_and_foreign_profile_is_hidden(self):
        owner = sign_up(self.signup_data(), Response(), self.session)
        other = sign_up(self.signup_data(name="Other User", email="other@example.com"), Response(), self.session)
        owner_user = self.session.get(User, owner.id)
        other_user = self.session.get(User, other.id)
        profile = create_profile(self.profile_data(), self.session, owner_user)
        self.assertEqual(profile.user_id, owner.id)
        self.assertEqual(get_profile(profile.id, self.session, owner_user).id, profile.id)
        with self.assertRaises(HTTPException) as error:
            get_profile(profile.id, self.session, other_user)
        self.assertEqual(error.exception.status_code, 404)

    def test_authenticated_profile_generates_and_serializes_careertwin(self):
        account = sign_up(self.signup_data(), Response(), self.session)
        user = self.session.get(User, account.id)
        profile = create_profile(self.profile_data(), self.session, user)
        twin = create_career_twin(profile.id, "IN", self.session, user)
        payload = twin.model_dump_json()
        self.assertIn('"development_plan"', payload)
        self.assertEqual(twin.profile.id, profile.id)
        token = create_session(self.session, user)
        current_user = current_user_dependency(request_with_cookie(token), self.session)
        self.assertEqual(me(current_user, self.session).profile_id, profile.id)

    def test_legacy_profiles_survive_migration_without_unsafe_auto_assignment(self):
        legacy_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        with legacy_engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE student_profiles (id INTEGER PRIMARY KEY, name VARCHAR(60) NOT NULL, "
                "education_level VARCHAR(40) NOT NULL, field_of_study VARCHAR(120) NOT NULL, "
                "skills JSON NOT NULL, interests JSON NOT NULL, work_preferences JSON NOT NULL, "
                "career_priorities JSON NOT NULL, created_at DATETIME NOT NULL)"
            ))
            connection.execute(text(
                "INSERT INTO student_profiles (id,name,education_level,field_of_study,skills,interests,work_preferences,career_priorities,created_at) "
                "VALUES (1,'Legacy','undergraduate','Economics','[]','[\"analytics\"]','[\"collaborative\"]','[\"growth\"]','2026-01-01 00:00:00')"
            ))
        with patch.object(database_module, "engine", legacy_engine), patch.object(
            database_module, "SessionLocal", sessionmaker(bind=legacy_engine, autoflush=False, expire_on_commit=False)
        ):
            database_module.create_database()
        columns = {column["name"] for column in inspect(legacy_engine).get_columns("student_profiles")}
        with legacy_engine.connect() as connection:
            row = connection.execute(text("SELECT id,name,user_id FROM student_profiles WHERE id=1")).one()
        self.assertIn("user_id", columns)
        self.assertEqual((row.id, row.name, row.user_id), (1, "Legacy", None))
        legacy_engine.dispose()

    def test_http_signup_profile_careertwin_ownership_and_logout_flow(self):
        invalid_status, _, invalid_body = self.http_request(
            "POST", "/api/auth/signup",
            {"name": "Nyra Shah", "email": "nyra@example.com", "password": "xY7!"},
        )
        self.assertEqual(invalid_status, 422)
        self.assertNotIn("xY7!", repr(invalid_body))

        signup_body = {"name": "Nyra Shah", "email": "nyra@example.com", "password": "CareerTwin!2026"}
        status_code, headers, account = self.http_request("POST", "/api/auth/signup", signup_body)
        self.assertEqual(status_code, 201)
        self.assertNotIn("password_hash", account)
        first_cookie = headers[b"set-cookie"].decode().split(";", 1)[0]

        unauthenticated_status, _, _ = self.http_request("GET", "/api/markets")
        self.assertEqual(unauthenticated_status, 401)
        profile_body = self.profile_data().model_dump(mode="json")
        profile_status, _, profile = self.http_request("POST", "/api/profiles", profile_body, first_cookie)
        self.assertEqual(profile_status, 201)
        profile_id = profile["id"]
        twin_status, _, twin = self.http_request(
            "POST", f"/api/profiles/{profile_id}/careertwin?market=IN", cookie=first_cookie
        )
        self.assertEqual(twin_status, 200)
        self.assertTrue(twin["career_options"][0]["development_plan"]["phases"])

        second_status, second_headers, _ = self.http_request(
            "POST", "/api/auth/signup",
            {"name": "Other User", "email": "other@example.com", "password": "CareerTwin!2026"},
        )
        self.assertEqual(second_status, 201)
        second_cookie = second_headers[b"set-cookie"].decode().split(";", 1)[0]
        foreign_status, _, _ = self.http_request("GET", f"/api/profiles/{profile_id}", cookie=second_cookie)
        self.assertEqual(foreign_status, 404)

        logout_status, _, _ = self.http_request("POST", "/api/auth/logout", cookie=first_cookie)
        self.assertEqual(logout_status, 204)
        after_logout, _, _ = self.http_request("GET", f"/api/profiles/{profile_id}", cookie=first_cookie)
        self.assertEqual(after_logout, 401)
        login_status, login_headers, restored_account = self.http_request(
            "POST", "/api/auth/login", {"email": "nyra@example.com", "password": "CareerTwin!2026"}
        )
        self.assertEqual(login_status, 200)
        self.assertEqual(restored_account["profile_id"], profile_id)
        restored_cookie = login_headers[b"set-cookie"].decode().split(";", 1)[0]
        restored_profile_status, _, restored_profile = self.http_request(
            "GET", f"/api/profiles/{profile_id}", cookie=restored_cookie
        )
        self.assertEqual(restored_profile_status, 200)
        self.assertEqual(restored_profile["id"], profile_id)


if __name__ == "__main__":
    unittest.main()
