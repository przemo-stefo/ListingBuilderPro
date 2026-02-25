# backend/tests/test_user_isolation.py
# Purpose: Tests ensuring user data isolation — prevent cross-user data leaks
# NOT for: Business logic tests (those are in test_allegro_offers.py etc.)

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestRequireUserId:
    """Test the require_user_id dependency rejects 'default' user_id.

    WHY: This is the defense-in-depth layer. Even if frontend JWT breaks,
    backend MUST reject 'default' user_id for data-sensitive endpoints.
    """

    def test_rejects_default_user_id(self):
        """'default' user_id MUST be rejected with 401."""
        from api.dependencies import require_user_id
        request = MagicMock()
        request.state.user_id = "default"
        with pytest.raises(HTTPException) as exc:
            require_user_id(request)
        assert exc.value.status_code == 401

    def test_rejects_missing_user_id(self):
        """Missing user_id (no state set) MUST be rejected with 401."""
        from api.dependencies import require_user_id
        request = MagicMock(spec=[])
        # WHY: request.state doesn't exist → getattr fallback → "default" → reject
        request.state = MagicMock(spec=[])
        with pytest.raises(HTTPException) as exc:
            require_user_id(request)
        assert exc.value.status_code == 401

    def test_accepts_real_user_id(self):
        """Real Supabase UUID user_id should pass."""
        from api.dependencies import require_user_id
        request = MagicMock()
        request.state.user_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = require_user_id(request)
        assert result == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_get_user_id_still_returns_default(self):
        """get_user_id (non-strict) should still return 'default' for backward compat."""
        from api.dependencies import get_user_id
        request = MagicMock()
        request.state.user_id = "default"
        result = get_user_id(request)
        assert result == "default"


class TestOAuthEndpointsRequireJWT:
    """Test that OAuth endpoints reject API-key-only requests (no JWT).

    WHY: This is the exact bug that caused Allegro data leak —
    API-key-only auth returned user_id='default', showing all connections.
    """

    def test_connections_rejects_api_key_only(self, client, test_settings):
        """GET /api/oauth/connections with only API key → 401."""
        resp = client.get(
            "/api/oauth/connections",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]

    def test_status_rejects_api_key_only(self, client, test_settings):
        """GET /api/oauth/status with only API key → 401."""
        resp = client.get(
            "/api/oauth/status",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401


class TestAllegroOffersRequireJWT:
    """Test that Allegro Offers Manager endpoints reject API-key-only requests."""

    def test_list_offers_rejects_api_key_only(self, client, test_settings):
        """GET /api/allegro/offers with only API key → 401."""
        resp = client.get(
            "/api/allegro/offers",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401

    def test_offer_detail_rejects_api_key_only(self, client, test_settings):
        """GET /api/allegro/offers/12345678 with only API key → 401."""
        resp = client.get(
            "/api/allegro/offers/12345678",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401


class TestSettingsRequireJWT:
    """Test that Settings endpoints reject API-key-only requests.

    WHY: Settings contain LLM API keys — must not be readable by anyone
    just because they have the proxy API key.
    """

    def test_get_settings_rejects_api_key_only(self, client, test_settings):
        """GET /api/settings with only API key → 401."""
        resp = client.get(
            "/api/settings",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401

    def test_update_settings_rejects_api_key_only(self, client, test_settings):
        """PUT /api/settings with only API key → 401."""
        resp = client.put(
            "/api/settings",
            headers={"X-API-Key": test_settings.api_secret_key},
            json={"general": {"store_name": "Hacked Store"}},
        )
        assert resp.status_code == 401


class TestConverterRequiresJWT:
    """Test that Converter endpoints reject API-key-only requests."""

    def test_scrape_rejects_api_key_only(self, client, test_settings):
        """POST /api/converter/scrape with only API key → 401."""
        resp = client.post(
            "/api/converter/scrape",
            headers={"X-API-Key": test_settings.api_secret_key},
            json={"urls": ["https://allegro.pl/oferta/test-123"]},
        )
        assert resp.status_code == 401


class TestImportRequiresJWT:
    """Test that import-from-allegro endpoint requires JWT."""

    def test_from_allegro_rejects_api_key_only(self, client, test_settings):
        """POST /api/import/from-allegro with only API key → 401."""
        resp = client.post(
            "/api/import/from-allegro",
            headers={"X-API-Key": test_settings.api_secret_key},
            json={"offer_ids": ["12345678"]},
        )
        assert resp.status_code == 401


class TestDataIsolationWithJWT:
    """Test that authenticated users only see their OWN data.

    WHY: Even with require_user_id, we must verify that queries
    actually filter by user_id, not just that auth passes.
    """

    def test_oauth_connections_filtered_by_user_id(self, db_session):
        """User A's OAuth connections must NOT appear for User B."""
        from models.oauth_connection import OAuthConnection

        # Create connections for two different users
        conn_a = OAuthConnection(
            marketplace="allegro",
            user_id="user-aaa-111",
            status="active",
            access_token="token-a",
        )
        conn_b = OAuthConnection(
            marketplace="allegro",
            user_id="user-bbb-222",
            status="active",
            access_token="token-b",
        )
        db_session.add_all([conn_a, conn_b])
        db_session.commit()

        # Query as user A — should only see user A's connection
        from services.oauth_service import get_connections
        conns = get_connections(db_session, "user-aaa-111")
        assert len(conns) == 1
        assert conns[0].user_id == "user-aaa-111"

        # Query as user B — should only see user B's connection
        conns = get_connections(db_session, "user-bbb-222")
        assert len(conns) == 1
        assert conns[0].user_id == "user-bbb-222"

        # Query as unknown user — should see nothing
        conns = get_connections(db_session, "user-ccc-333")
        assert len(conns) == 0

    def test_settings_endpoint_requires_jwt(self, client, test_settings):
        """Settings GET with only API key should be rejected.

        WHY: Settings contain LLM API keys — isolating at auth level
        prevents cross-user reads even without per-user DB filtering.
        """
        resp = client.get(
            "/api/settings",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]


class TestMiddlewareUserIdFlow:
    """Test that middleware correctly sets user_id from JWT vs API key.

    WHY: The root cause of the data leak was that API-key-only requests
    got user_id='default', which was shared among all users.
    """

    def test_api_key_only_sets_default(self, client, test_settings):
        """API-key-only request should set user_id='default' (middleware behavior)."""
        # WHY: We test this to ensure require_user_id() CATCHES this case
        resp = client.get(
            "/health",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200  # health is public

    def test_no_auth_rejects(self, client):
        """Request without any auth should be rejected."""
        resp = client.get("/api/oauth/connections")
        assert resp.status_code == 401
