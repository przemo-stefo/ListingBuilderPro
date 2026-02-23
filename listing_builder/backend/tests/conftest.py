# backend/tests/conftest.py
# Purpose: Shared test fixtures — TestSettings, SQLite DB, FastAPI TestClient
# NOT for: Individual test logic

import os
import sys
import pytest

# WHY: backend/ is the import root for the app — add it to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# WHY: Set env vars BEFORE config.py is imported (it reads them at module level).
# This prevents database.py from failing on SQLite-incompatible PG pool args.
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-minimum-16")
os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret-min16")
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "fake-supabase-key-value")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key-val")
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost:5432/fakedb")
os.environ.setdefault("GROQ_API_KEY", "gsk_fake_key_1234567")


class TestSettings:
    """Fake settings object that satisfies all attribute access."""
    app_env = "development"
    app_debug = False
    api_secret_key = "test-secret-key-minimum-16"
    cors_origins = "http://localhost:3000"
    supabase_url = "https://fake.supabase.co"
    supabase_key = "fake-supabase-key-value"
    supabase_service_key = "fake-service-key-val"
    database_url = "postgresql://fake:fake@localhost:5432/fakedb"
    groq_model = "llama-3.3-70b-versatile"
    groq_api_key = "gsk_fake_key_1234567"
    groq_api_key_2 = "gsk_fake_key_2"
    groq_api_key_3 = ""
    groq_api_key_4 = ""
    groq_api_key_5 = ""
    groq_api_key_6 = ""
    groq_api_key_7 = ""
    groq_api_key_8 = ""
    amazon_refresh_token = ""
    amazon_client_id = ""
    amazon_client_secret = ""
    amazon_region = "eu-west-1"
    ebay_app_id = ""
    ebay_cert_id = ""
    ebay_dev_id = ""
    ebay_ru_name = ""
    allegro_client_id = ""
    allegro_client_secret = ""
    bol_client_id = ""
    bol_client_secret = ""
    kaufland_client_key = ""
    kaufland_secret_key = ""
    rag_mode = "hybrid"
    cf_account_id = ""
    cf_auth_email = ""
    cf_api_key = ""
    scrape_do_token = ""
    scraper_proxy_url = ""
    n8n_webhook_url = ""
    n8n_webhook_secret = ""
    stripe_secret_key = ""
    stripe_price_monthly = ""
    stripe_webhook_secret = "whsec_test_secret"
    supabase_jwt_secret = "test-jwt-secret-minimum-32-chars!"
    admin_emails = "admin@test.com"
    webhook_secret = "test-webhook-secret-min16"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self):
        return self.app_env == "production"

    @property
    def admin_emails_list(self):
        if not self.admin_emails:
            return []
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def groq_api_keys(self):
        keys = [self.groq_api_key]
        for attr in ("groq_api_key_2", "groq_api_key_3", "groq_api_key_4",
                      "groq_api_key_5", "groq_api_key_6", "groq_api_key_7",
                      "groq_api_key_8"):
            val = getattr(self, attr, "")
            if val:
                keys.append(val)
        return keys


_test_settings = TestSettings()


@pytest.fixture
def test_settings():
    return _test_settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Patch config.settings globally for tests that import it."""
    monkeypatch.setattr("config.settings", _test_settings)
    return _test_settings


# --- SQLite in-memory DB for integration tests ---

from sqlalchemy import create_engine, event, String as SAString
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import JSON

# WHY: StaticPool ensures all connections share the same in-memory SQLite DB.
# Without it, each connection gets its own empty database.
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# WHY: PostgreSQL types (ARRAY, JSONB, PG_UUID) don't compile on SQLite.
_pg_patched = False

def _patch_pg_columns_once():
    """Replace PG-specific column types with SQLite-compatible ones."""
    global _pg_patched
    if _pg_patched:
        return
    from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB, UUID as PG_UUID
    from sqlalchemy import ARRAY as SA_ARRAY
    from database import Base
    import models  # noqa: F401 — register all model tables
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, (PG_ARRAY, SA_ARRAY)):
                col.type = JSON()
            elif isinstance(col.type, JSONB):
                col.type = JSON()
            elif isinstance(col.type, PG_UUID):
                col.type = SAString(36)
    _pg_patched = True


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture
def db_session(mock_settings):
    """Yield a clean SQLite session with tables created/dropped per test."""
    from database import Base
    _patch_pg_columns_once()
    Base.metadata.create_all(bind=_test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client(mock_settings, db_session):
    """FastAPI TestClient with overridden DB and settings."""
    from fastapi.testclient import TestClient
    from database import get_db

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    from main import app
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
