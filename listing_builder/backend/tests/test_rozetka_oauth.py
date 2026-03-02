# backend/tests/test_rozetka_oauth.py
# Purpose: Full test suite for Rozetka OAuth (credentials-based) flow
# NOT for: AliExpress/Temu OAuth tests (those need app keys)

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from tests.conftest import TEST_USER_ID


class TestRozetkaConnectEndpoint:
    """HTTP-level tests for POST /api/oauth/rozetka/connect."""

    def test_rozetka_connect_no_auth_401(self, client):
        """Endpoint requires JWT — anonymous request should be rejected."""
        resp = client.post("/api/oauth/rozetka/connect", json={
            "username": "seller@rozetka.com",
            "password": "secret123",
        })
        assert resp.status_code == 401

    def test_rozetka_connect_empty_username_422(self, auth_client, test_settings):
        """Empty username should fail validation."""
        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "", "password": "secret123"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 422

    def test_rozetka_connect_empty_password_422(self, auth_client, test_settings):
        """Empty password should fail validation."""
        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rozetka.com", "password": "  "},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 422

    def test_rozetka_connect_missing_fields_422(self, auth_client, test_settings):
        """Missing required fields should fail validation."""
        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 422

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_connect_success(self, mock_client_cls, auth_client, test_settings, db_session):
        """Valid credentials → Rozetka API returns token → connection saved."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "content": {"access_token": "rz_token_abc123"}
        }
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rozetka.com", "password": "correct_pass"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "connected"
        assert data["marketplace"] == "rozetka"

        # WHY: Verify connection was persisted in DB
        from models.oauth_connection import OAuthConnection
        conn = db_session.query(OAuthConnection).filter(
            OAuthConnection.user_id == TEST_USER_ID,
            OAuthConnection.marketplace == "rozetka",
        ).first()
        assert conn is not None
        assert conn.status == "active"
        assert conn.access_token == "rz_token_abc123"

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_connect_bad_credentials_400(self, mock_client_cls, auth_client, test_settings):
        """Invalid credentials → Rozetka API returns non-200 → 400 error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "bad@user.com", "password": "wrong"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400
        assert "Nieprawidłowe dane Rozetka" in resp.json()["detail"]

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_connect_no_token_400(self, mock_client_cls, auth_client, test_settings):
        """Rozetka returns 200 but no token in response → 400 error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": {}}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        resp = auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rozetka.com", "password": "pass"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400
        assert "nie zwróciła tokenu" in resp.json()["detail"]


class TestRozetkaConnectionLifecycle:
    """Test connection listing, status, and disconnect for Rozetka."""

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_shows_in_connections(self, mock_client_cls, auth_client, test_settings, db_session):
        """After connecting Rozetka, it should appear in /oauth/connections."""
        # Setup: create Rozetka connection
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": {"access_token": "rz_tok"}}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rz.com", "password": "pass"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )

        # Verify: list connections
        resp = auth_client.get(
            "/api/oauth/connections",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        conns = resp.json()["connections"]
        rozetka = [c for c in conns if c["marketplace"] == "rozetka"]
        assert len(rozetka) == 1
        assert rozetka[0]["status"] == "active"

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_disconnect(self, mock_client_cls, auth_client, test_settings, db_session):
        """After connecting Rozetka, DELETE /oauth/rozetka should disconnect."""
        # Setup: create connection
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": {"access_token": "rz_tok"}}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rz.com", "password": "pass"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )

        # Disconnect
        resp = auth_client.delete(
            "/api/oauth/rozetka",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "disconnected"

        # Verify: no longer in connections
        resp = auth_client.get(
            "/api/oauth/connections",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        conns = resp.json()["connections"]
        rozetka = [c for c in conns if c["marketplace"] == "rozetka"]
        assert len(rozetka) == 0

    def test_rozetka_disconnect_nonexistent_404(self, auth_client, test_settings):
        """Disconnect without prior connection should return 404."""
        resp = auth_client.delete(
            "/api/oauth/rozetka",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 404


class TestRozetkaConnectionOverwrite:
    """Test reconnect (overwrite existing connection)."""

    @patch("services.oauth_service.httpx.AsyncClient")
    def test_rozetka_reconnect_overwrites(self, mock_client_cls, auth_client, test_settings, db_session):
        """Connecting again should overwrite the existing connection, not create a duplicate."""
        # First connect
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": {"access_token": "old_token"}}
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value.put = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rz.com", "password": "pass1"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )

        # Second connect with new credentials
        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {"content": {"access_token": "new_token"}}
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__.return_value.put = AsyncMock(return_value=mock_resp2)
        mock_client_cls.return_value = mock_ctx2

        auth_client.post(
            "/api/oauth/rozetka/connect",
            json={"username": "seller@rz.com", "password": "pass2"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )

        # Verify: only 1 connection, with new token
        from models.oauth_connection import OAuthConnection
        conns = db_session.query(OAuthConnection).filter(
            OAuthConnection.user_id == TEST_USER_ID,
            OAuthConnection.marketplace == "rozetka",
        ).all()
        assert len(conns) == 1
        assert conns[0].access_token == "new_token"


class TestScraperRemoved:
    """Verify AliExpress/Temu/Rozetka scraper endpoints return proper errors."""

    def test_rozetka_scrape_url_returns_400(self, auth_client, test_settings):
        """Rozetka URL scraping should return 400 — scraper removed."""
        resp = auth_client.post(
            "/api/import/scrape-url",
            json={"url": "https://rozetka.com.ua/ua/test-product/p12345/"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400
        assert "nie jest wspierany" in resp.json()["detail"]
        assert "OAuth" in resp.json()["detail"]

    def test_aliexpress_scrape_url_returns_400(self, auth_client, test_settings):
        """AliExpress URL scraping should return 400 — scraper removed."""
        resp = auth_client.post(
            "/api/import/scrape-url",
            json={"url": "https://aliexpress.com/item/1005001234567.html"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400
        assert "nie jest wspierany" in resp.json()["detail"]

    def test_temu_scrape_url_returns_400(self, auth_client, test_settings):
        """Temu URL scraping should return 400 — scraper removed."""
        resp = auth_client.post(
            "/api/import/scrape-url",
            json={"url": "https://temu.com/goods-detail-g-123456.html"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400
        assert "nie jest wspierany" in resp.json()["detail"]
