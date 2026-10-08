import unittest
from unittest.mock import patch

from fastapi import Response

from app.api.auth_routes import _set_session_cookie
from app.db.database import _database_url
from app.main import _cors_origins, root_health_check


class ProductionConfigurationTests(unittest.TestCase):
    def test_database_url_supports_local_sqlite_and_postgres_provider_schemes(self):
        with patch.dict("os.environ", {"DATABASE_URL": "sqlite:///./local.db"}, clear=True):
            self.assertEqual(_database_url(), "sqlite:///./local.db")
        with patch.dict("os.environ", {"DATABASE_URL": "postgres://user:secret@host/db"}, clear=True):
            self.assertEqual(_database_url(), "postgresql+psycopg://user:secret@host/db")
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://user:secret@host/db"}, clear=True):
            self.assertEqual(_database_url(), "postgresql+psycopg://user:secret@host/db")

    def test_cors_uses_explicit_origins_and_rejects_wildcards(self):
        with patch.dict("os.environ", {"CORS_ORIGINS": " https://app.example.com/ ,https://admin.example.com "}, clear=True):
            self.assertEqual(_cors_origins(), ["https://app.example.com", "https://admin.example.com"])
        with patch.dict("os.environ", {"CORS_ORIGINS": "*"}, clear=True):
            with self.assertRaises(RuntimeError):
                _cors_origins()

    def test_production_session_cookie_is_secure_by_default(self):
        with patch.dict("os.environ", {"CAREERTWIN_ENVIRONMENT": "production"}, clear=True):
            response = Response()
            _set_session_cookie(response, "opaque-session-token")
        cookie = response.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("secure", cookie)
        self.assertIn("samesite=lax", cookie)

    def test_root_health_endpoint_is_minimal(self):
        self.assertEqual(root_health_check(), {"status": "ok"})
