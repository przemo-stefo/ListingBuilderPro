# backend/tests/test_security_headers.py
# Purpose: Verify security headers are set on all responses
# NOT for: Auth or business logic

import pytest


class TestSecurityHeaders:
    """SecurityHeadersMiddleware should add OWASP headers to every response."""

    def test_hsts_header(self, client):
        resp = client.get("/health")
        assert "Strict-Transport-Security" in resp.headers
        assert "max-age=" in resp.headers["Strict-Transport-Security"]

    def test_content_type_nosniff(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_frame_deny(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_xss_protection(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_csp_header(self, client):
        resp = client.get("/health")
        assert "Content-Security-Policy" in resp.headers

    def test_referrer_policy(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_headers_on_protected_endpoint(self, client, test_settings):
        resp = client.get("/api/products", headers={"X-API-Key": test_settings.api_secret_key})
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
