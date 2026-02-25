# backend/tests/test_stripe_routes.py
# Purpose: Stripe route HTTP tests — checkout, validate, recover, webhook
# NOT for: Stripe API logic (see test_stripe_service.py)

import pytest
from unittest.mock import patch, MagicMock
from models.premium_license import PremiumLicense
from tests.conftest import TEST_USER_EMAIL


class TestValidateLicenseRoute:

    def test_validate_invalid_key(self, client, test_settings):
        resp = client.post(
            "/api/stripe/validate-license",
            json={"license_key": "nonexistent-key-1234"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["tier"] == "free"

    def test_validate_active_key(self, client, test_settings, db_session):
        lic = PremiumLicense(
            email="user@test.com",
            license_key="route-test-valid-key",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()

        resp = client.post(
            "/api/stripe/validate-license",
            json={"license_key": "route-test-valid-key"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True
        assert resp.json()["tier"] == "premium"

    def test_validate_short_key_rejected(self, client, test_settings):
        resp = client.post(
            "/api/stripe/validate-license",
            json={"license_key": "short"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 422


class TestRecoverLicenseRoute:

    def test_recover_no_jwt_rejects(self, client, test_settings):
        """WHY: recover-license requires JWT — API key only should be rejected."""
        resp = client.post(
            "/api/stripe/recover-license",
            json={"email": "nobody@test.com"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401

    def test_recover_no_license(self, auth_client):
        """No license for this email → found=False."""
        resp = auth_client.post(
            "/api/stripe/recover-license",
            json={"email": TEST_USER_EMAIL},
        )
        assert resp.status_code == 200
        assert resp.json()["found"] is False

    def test_recover_existing_license(self, auth_client, db_session):
        lic = PremiumLicense(
            email=TEST_USER_EMAIL,
            license_key="recover-test-key-123",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()

        resp = auth_client.post(
            "/api/stripe/recover-license",
            json={"email": TEST_USER_EMAIL},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["license_key"] == "recover-test-key-123"

    def test_recover_wrong_email_rejects(self, auth_client):
        """WHY: JWT email must match request email — prevents stealing keys."""
        resp = auth_client.post(
            "/api/stripe/recover-license",
            json={"email": "someone_else@test.com"},
        )
        assert resp.status_code == 403


class TestSessionLicenseRoute:

    def test_session_no_jwt_rejects(self, client, test_settings):
        """WHY: session-license requires JWT — prevents session_id theft."""
        resp = client.get(
            "/api/stripe/session/cs_nonexistent/license",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 401

    def test_session_not_found(self, auth_client):
        resp = auth_client.get("/api/stripe/session/cs_nonexistent/license")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_session_found(self, auth_client, db_session):
        lic = PremiumLicense(
            email="session@test.com",
            license_key="session-route-key-12",
            stripe_checkout_session_id="cs_route_test",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()

        resp = auth_client.get("/api/stripe/session/cs_route_test/license")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["license_key"] == "session-route-key-12"


class TestWebhookRoute:

    def test_webhook_missing_signature(self, client):
        resp = client.post("/api/stripe/webhook", content=b"raw body")
        assert resp.status_code == 400

    # WHY: Patch in the module where it's USED (route imported it at top level)
    @patch("api.stripe_routes.handle_webhook_event")
    def test_webhook_valid_signature(self, mock_handle, client):
        mock_handle.return_value = "checkout.session.completed"
        resp = client.post(
            "/api/stripe/webhook",
            content=b"raw body",
            headers={"stripe-signature": "t=123,v1=abc"},
        )
        assert resp.status_code == 200


class TestCheckoutRoute:

    @patch("api.stripe_routes.create_checkout_session")
    def test_create_checkout(self, mock_create, client, test_settings):
        mock_create.return_value = "https://checkout.stripe.com/test"
        resp = client.post(
            "/api/stripe/create-checkout",
            json={"plan_type": "monthly", "email": "test@example.com"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert "checkout_url" in resp.json()
