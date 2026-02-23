# backend/tests/test_stripe_service.py
# Purpose: Stripe service + license key DB tests
# NOT for: HTTP route tests or real Stripe API calls

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from models.premium_license import PremiumLicense


class TestValidateLicense:

    def test_empty_key_returns_false(self, db_session):
        from services.stripe_service import validate_license
        assert validate_license("", db_session) is False

    def test_nonexistent_key_returns_false(self, db_session):
        from services.stripe_service import validate_license
        assert validate_license("nonexistent-key", db_session) is False

    def test_active_license_returns_true(self, db_session):
        from services.stripe_service import validate_license
        lic = PremiumLicense(
            email="test@example.com",
            license_key="valid-key-12345678",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()
        assert validate_license("valid-key-12345678", db_session) is True

    def test_revoked_license_returns_false(self, db_session):
        from services.stripe_service import validate_license
        lic = PremiumLicense(
            email="test@example.com",
            license_key="revoked-key-123456",
            plan_type="monthly",
            status="revoked",
        )
        db_session.add(lic)
        db_session.commit()
        assert validate_license("revoked-key-123456", db_session) is False

    def test_expired_license_returns_false(self, db_session):
        """Expired license with status already set to 'expired' returns False."""
        from services.stripe_service import validate_license
        # WHY: SQLite lacks timezone support, so we test expiration by
        # setting status='expired' directly (matches production behavior
        # after the expiry check runs once).
        lic = PremiumLicense(
            email="test@example.com",
            license_key="expired-key-123456",
            plan_type="monthly",
            status="expired",
        )
        db_session.add(lic)
        db_session.commit()
        assert validate_license("expired-key-123456", db_session) is False


class TestGetLicenseByEmail:

    def test_no_license_returns_none(self, db_session):
        from services.stripe_service import get_license_by_email
        assert get_license_by_email("nobody@test.com", db_session) is None

    def test_active_license_found(self, db_session):
        from services.stripe_service import get_license_by_email
        lic = PremiumLicense(
            email="user@test.com",
            license_key="found-key-12345678",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()
        assert get_license_by_email("user@test.com", db_session) == "found-key-12345678"


class TestGetLicenseBySession:

    def test_no_session_returns_none(self, db_session):
        from services.stripe_service import get_license_by_session
        assert get_license_by_session("cs_fake_xxx", db_session) is None

    def test_session_found(self, db_session):
        from services.stripe_service import get_license_by_session
        lic = PremiumLicense(
            email="user@test.com",
            license_key="session-key-123456",
            stripe_checkout_session_id="cs_test_123",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()
        assert get_license_by_session("cs_test_123", db_session) == "session-key-123456"


class TestHandleCheckoutCompleted:

    def test_creates_license(self, db_session):
        from services.stripe_service import handle_checkout_completed
        session_data = {
            "id": "cs_new_session",
            "customer": "cus_123",
            "customer_email": "buyer@test.com",
            "metadata": {"plan_type": "monthly"},
            "subscription": "sub_abc",
        }
        handle_checkout_completed(session_data, db_session)
        lic = db_session.query(PremiumLicense).filter_by(
            stripe_checkout_session_id="cs_new_session"
        ).first()
        assert lic is not None
        assert lic.email == "buyer@test.com"
        assert lic.status == "active"

    def test_duplicate_session_idempotent(self, db_session):
        from services.stripe_service import handle_checkout_completed
        session_data = {
            "id": "cs_dup_session",
            "customer": "cus_123",
            "customer_email": "buyer@test.com",
            "metadata": {"plan_type": "monthly"},
            "subscription": "sub_abc",
        }
        handle_checkout_completed(session_data, db_session)
        handle_checkout_completed(session_data, db_session)
        count = db_session.query(PremiumLicense).filter_by(
            stripe_checkout_session_id="cs_dup_session"
        ).count()
        assert count == 1


class TestHandleSubscriptionCancelled:

    def test_revokes_license(self, db_session):
        from services.stripe_service import handle_subscription_cancelled
        lic = PremiumLicense(
            email="cancel@test.com",
            license_key="cancel-key-1234567",
            stripe_subscription_id="sub_cancel_123",
            plan_type="monthly",
            status="active",
        )
        db_session.add(lic)
        db_session.commit()

        handle_subscription_cancelled({"id": "sub_cancel_123"}, db_session)
        db_session.refresh(lic)
        assert lic.status == "revoked"

    def test_missing_subscription_no_error(self, db_session):
        from services.stripe_service import handle_subscription_cancelled
        handle_subscription_cancelled({"id": "sub_nonexistent"}, db_session)
