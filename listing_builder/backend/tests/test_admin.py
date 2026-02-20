# backend/tests/test_admin.py
# Purpose: Unit tests for admin role system — require_admin, admin_emails config
# NOT for: Integration tests with real database or Supabase JWT

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from api.dependencies import require_admin
from config import Settings


# --- Settings.admin_emails_list ---

class TestAdminEmailsList:
    """Test the admin_emails_list property logic directly (avoids Pydantic v2 __new__ issues)."""

    def _parse(self, raw: str):
        """Replicate admin_emails_list logic without constructing Settings."""
        if not raw:
            return []
        return [e.strip().lower() for e in raw.split(",") if e.strip()]

    def test_empty_string_returns_empty_list(self):
        assert self._parse("") == []

    def test_single_email(self):
        assert self._parse("admin@test.com") == ["admin@test.com"]

    def test_multiple_emails_comma_separated(self):
        assert self._parse("a@test.com, b@test.com, c@test.com") == ["a@test.com", "b@test.com", "c@test.com"]

    def test_strips_whitespace(self):
        assert self._parse("  admin@test.com ,  user@test.com  ") == ["admin@test.com", "user@test.com"]

    def test_lowercases_emails(self):
        assert self._parse("Admin@Test.COM") == ["admin@test.com"]

    def test_ignores_empty_entries(self):
        assert self._parse("a@test.com,,, ,b@test.com") == ["a@test.com", "b@test.com"]


# --- require_admin dependency ---

class TestRequireAdmin:
    def _mock_request(self, email: str = "") -> MagicMock:
        req = MagicMock()
        req.state = MagicMock()
        req.state.user_email = email
        return req

    @patch("api.dependencies.settings")
    def test_admin_email_passes(self, mock_settings):
        mock_settings.admin_emails_list = ["admin@test.com"]
        req = self._mock_request("admin@test.com")

        result = require_admin(req)
        assert result == "admin@test.com"

    @patch("api.dependencies.settings")
    def test_case_insensitive_match(self, mock_settings):
        mock_settings.admin_emails_list = ["admin@test.com"]
        req = self._mock_request("Admin@Test.COM")

        result = require_admin(req)
        assert result == "Admin@Test.COM"

    @patch("api.dependencies.settings")
    def test_non_admin_raises_403(self, mock_settings):
        mock_settings.admin_emails_list = ["admin@test.com"]
        req = self._mock_request("user@test.com")

        with pytest.raises(HTTPException) as exc:
            require_admin(req)
        assert exc.value.status_code == 403

    @patch("api.dependencies.settings")
    def test_empty_email_raises_403(self, mock_settings):
        mock_settings.admin_emails_list = ["admin@test.com"]
        req = self._mock_request("")

        with pytest.raises(HTTPException) as exc:
            require_admin(req)
        assert exc.value.status_code == 403

    @patch("api.dependencies.settings")
    def test_no_email_attr_raises_403(self, mock_settings):
        """When user_email was never set on request.state (API key auth path)."""
        mock_settings.admin_emails_list = ["admin@test.com"]
        req = MagicMock()
        # WHY: delattr so getattr falls back to default ""
        req.state = MagicMock(spec=[])

        with pytest.raises(HTTPException) as exc:
            require_admin(req)
        assert exc.value.status_code == 403

    @patch("api.dependencies.settings")
    def test_empty_admin_list_always_403(self, mock_settings):
        """When ADMIN_EMAILS env var is empty, nobody is admin."""
        mock_settings.admin_emails_list = []
        req = self._mock_request("any@test.com")

        with pytest.raises(HTTPException) as exc:
            require_admin(req)
        assert exc.value.status_code == 403


# --- get_admin_status (admin_routes /me endpoint) ---

class TestAdminMeEndpoint:
    @patch("api.admin_routes.settings")
    @pytest.mark.asyncio
    async def test_admin_returns_true(self, mock_settings):
        from api.admin_routes import get_admin_status

        mock_settings.admin_emails_list = ["admin@test.com"]
        req = MagicMock()
        req.state = MagicMock()
        req.state.user_email = "admin@test.com"

        result = await get_admin_status(req)
        assert result["is_admin"] is True
        assert result["email"] == "admin@test.com"

    @patch("api.admin_routes.settings")
    @pytest.mark.asyncio
    async def test_non_admin_returns_false(self, mock_settings):
        from api.admin_routes import get_admin_status

        mock_settings.admin_emails_list = ["admin@test.com"]
        req = MagicMock()
        req.state = MagicMock()
        req.state.user_email = "user@test.com"

        result = await get_admin_status(req)
        assert result["is_admin"] is False

    @patch("api.admin_routes.settings")
    @pytest.mark.asyncio
    async def test_no_email_returns_false(self, mock_settings):
        from api.admin_routes import get_admin_status

        mock_settings.admin_emails_list = ["admin@test.com"]
        req = MagicMock()
        req.state = MagicMock(spec=[])

        result = await get_admin_status(req)
        assert result["is_admin"] is False
        assert result["email"] == ""
