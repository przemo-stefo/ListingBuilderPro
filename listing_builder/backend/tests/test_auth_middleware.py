# backend/tests/test_auth_middleware.py
# Purpose: API key + JWT authentication middleware tests
# NOT for: Business logic or route-specific tests

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from starlette.testclient import TestClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse


class TestVerifyApiKey:
    """Test the verify_api_key dependency function."""

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self):
        from middleware.auth import verify_api_key
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await verify_api_key(None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_key_raises_401(self, mock_settings):
        from middleware.auth import verify_api_key
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await verify_api_key("wrong-key-here-1234567")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_key_returns_key(self, mock_settings):
        from middleware.auth import verify_api_key
        result = await verify_api_key(mock_settings.api_secret_key)
        assert result == mock_settings.api_secret_key


class TestAPIKeyMiddleware:
    """Test the APIKeyMiddleware dispatch logic."""

    def test_public_paths_allowed(self):
        from middleware.auth import APIKeyMiddleware
        public = APIKeyMiddleware.PUBLIC_PATHS
        assert "/health" in public
        assert "/" in public
        assert "/api/stripe/webhook" in public
        assert "/api/import/webhook" in public
        assert "/api/auth/me" in public

    def test_health_endpoint_no_auth(self, client):
        """Health endpoint is public — no API key needed."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_root_endpoint_no_auth(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"

    def test_protected_endpoint_rejects_no_key(self, client):
        resp = client.get("/api/products")
        assert resp.status_code == 401

    def test_protected_endpoint_rejects_bad_key(self, client):
        resp = client.get("/api/products", headers={"X-API-Key": "bad-key"})
        assert resp.status_code == 401

    def test_protected_endpoint_accepts_valid_key(self, auth_client, test_settings):
        # WHY: auth_client mocks JWT so require_user_id passes too
        resp = auth_client.get(
            "/api/products",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        # 200 = API key middleware + JWT auth both passed
        assert resp.status_code == 200
