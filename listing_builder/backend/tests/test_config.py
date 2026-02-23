# backend/tests/test_config.py
# Purpose: Test Settings validation — weak secrets, env validation, properties

import pytest
from pydantic import ValidationError


def _make_env(**overrides):
    """Build minimal valid env dict, with optional overrides."""
    base = {
        "api_secret_key": "a-very-secure-secret-key-123",
        "webhook_secret": "webhook-secret-key-123456",
        "supabase_url": "https://x.supabase.co",
        "supabase_key": "sb-key",
        "supabase_service_key": "sb-svc-key",
        "database_url": "postgresql://u:p@localhost/db",
        "groq_api_key": "gsk_test_key",
    }
    base.update(overrides)
    return base


class TestSettingsValidation:

    def test_valid_settings_load(self):
        from config import Settings
        s = Settings(**_make_env())
        assert s.api_secret_key == "a-very-secure-secret-key-123"

    def test_weak_api_secret_rejected(self):
        from config import Settings
        with pytest.raises(ValidationError, match="weak"):
            Settings(**_make_env(api_secret_key="change-me"))

    def test_short_api_secret_rejected(self):
        from config import Settings
        with pytest.raises(ValidationError, match="at least 16"):
            Settings(**_make_env(api_secret_key="short"))

    def test_weak_webhook_secret_rejected(self):
        from config import Settings
        with pytest.raises(ValidationError, match="weak"):
            Settings(**_make_env(webhook_secret="password"))

    def test_invalid_app_env_rejected(self):
        from config import Settings
        with pytest.raises(ValidationError, match="must be one of"):
            Settings(**_make_env(app_env="invalid"))

    def test_valid_app_env_values(self):
        from config import Settings
        for env in ("development", "staging", "production"):
            s = Settings(**_make_env(app_env=env))
            assert s.app_env == env


class TestSettingsProperties:

    def test_cors_origins_list(self):
        from config import Settings
        s = Settings(**_make_env(cors_origins="http://a.com, http://b.com"))
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_is_production_true(self):
        from config import Settings
        s = Settings(**_make_env(app_env="production"))
        assert s.is_production is True

    def test_is_production_false(self):
        from config import Settings
        s = Settings(**_make_env(app_env="development"))
        assert s.is_production is False

    def test_admin_emails_list_empty(self):
        from config import Settings
        s = Settings(**_make_env(admin_emails=""))
        assert s.admin_emails_list == []

    def test_admin_emails_list_parsed(self):
        from config import Settings
        s = Settings(**_make_env(admin_emails="A@b.com, C@D.com"))
        assert s.admin_emails_list == ["a@b.com", "c@d.com"]

    def test_groq_api_keys_rotation(self):
        from config import Settings
        s = Settings(**_make_env(groq_api_key_2="key2", groq_api_key_3="key3"))
        assert len(s.groq_api_keys) == 3
        assert s.groq_api_keys[0] == "gsk_test_key"
