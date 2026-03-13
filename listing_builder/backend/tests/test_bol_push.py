# backend/tests/test_bol_push.py
# Purpose: Tests for BOL.com offer push (create via Retailer API v10)
# NOT for: BOL scraper or CSV export tests (those are in test_bol_converter.py)

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from services.bol_api import _build_offer_payload, push_bol_offer


# ── _build_offer_payload ─────────────────────────────────────────────

class TestBuildOfferPayload:

    def _sample_fields(self):
        return {
            "ean": "5901234567890",
            "sku": "ALG-12345",
            "condition": "NEW",
            "title": "Nike Air Max 90 Sportschoenen",
            "price": "99.99",
            "stock": "10",
            "delivery_code": "3-5d",
        }

    def test_basic_structure(self):
        payload = _build_offer_payload(self._sample_fields())

        assert payload["ean"] == "5901234567890"
        assert payload["reference"] == "ALG-12345"
        assert payload["condition"] == {"name": "NEW"}
        assert payload["onHoldByRetailer"] is False

    def test_pricing_bundle(self):
        payload = _build_offer_payload(self._sample_fields())

        prices = payload["pricing"]["bundlePrices"]
        assert len(prices) == 1
        assert prices[0]["quantity"] == 1
        assert prices[0]["unitPrice"] == 99.99

    def test_stock_amount(self):
        payload = _build_offer_payload(self._sample_fields())

        assert payload["stock"]["amount"] == 10
        assert payload["stock"]["managedByRetailer"] is True

    def test_fulfilment_fbr(self):
        payload = _build_offer_payload(self._sample_fields())

        assert payload["fulfilment"]["method"] == "FBR"
        assert payload["fulfilment"]["deliveryCode"] == "3-5d"

    def test_unknown_product_title(self):
        payload = _build_offer_payload(self._sample_fields())
        assert payload["unknownProductTitle"] == "Nike Air Max 90 Sportschoenen"

    def test_empty_price_defaults_zero(self):
        fields = self._sample_fields()
        fields["price"] = ""
        payload = _build_offer_payload(fields)
        assert payload["pricing"]["bundlePrices"][0]["unitPrice"] == 0

    def test_empty_stock_defaults_one(self):
        fields = self._sample_fields()
        fields["stock"] = ""
        payload = _build_offer_payload(fields)
        assert payload["stock"]["amount"] == 1

    def test_price_rounded(self):
        fields = self._sample_fields()
        fields["price"] = "29.999"
        payload = _build_offer_payload(fields)
        assert payload["pricing"]["bundlePrices"][0]["unitPrice"] == 30.0


# ── push_bol_offer ───────────────────────────────────────────────────

class TestPushBolOffer:

    @pytest.mark.asyncio
    async def test_no_connection_returns_error(self, mock_settings, db_session):
        """WHY: User hasn't connected BOL — should get clear error."""
        result = await push_bol_offer(db_session, "user-123", {"ean": "123"})
        assert result["success"] is False
        assert "nie jest połączony" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_ean_returns_error(self, mock_settings, db_session):
        """WHY: EAN check happens after connection check, so we need an active connection."""
        from models.oauth_connection import OAuthConnection
        from datetime import datetime, timedelta

        conn = OAuthConnection(
            user_id="user-ean-test",
            marketplace="bol",
            status="active",
            access_token="test-token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            raw_data={"client_id": "test", "client_secret": "test"},
        )
        db_session.add(conn)
        db_session.commit()

        result = await push_bol_offer(db_session, "user-ean-test", {"title": "Test"})
        assert result["success"] is False
        assert "EAN" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_push(self, mock_settings, db_session):
        """WHY: Happy path — active connection, valid fields, BOL returns 202."""
        from models.oauth_connection import OAuthConnection
        from datetime import datetime, timedelta

        conn = OAuthConnection(
            user_id="user-push-test",
            marketplace="bol",
            status="active",
            access_token="test-token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            raw_data={"client_id": "test", "client_secret": "test"},
        )
        db_session.add(conn)
        db_session.commit()

        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.json.return_value = {"processStatusId": "ps-12345"}

        with patch("services.bol_api.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await push_bol_offer(
                db_session, "user-push-test",
                {"ean": "5901234567890", "price": "29.99", "stock": "5",
                 "condition": "NEW", "sku": "ALG-999", "title": "Test",
                 "delivery_code": "3-5d"},
            )

        assert result["success"] is True
        assert result["processStatusId"] == "ps-12345"
        assert result["ean"] == "5901234567890"

    @pytest.mark.asyncio
    async def test_bol_api_error_parsed(self, mock_settings, db_session):
        """WHY: BOL returns violations — we should extract readable error."""
        from models.oauth_connection import OAuthConnection
        from datetime import datetime, timedelta

        conn = OAuthConnection(
            user_id="user-err-test",
            marketplace="bol",
            status="active",
            access_token="test-token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            raw_data={"client_id": "test", "client_secret": "test"},
        )
        db_session.add(conn)
        db_session.commit()

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "violations": [{"reason": "EAN is invalid"}]
        }
        mock_resp.text = ""

        with patch("services.bol_api.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await push_bol_offer(
                db_session, "user-err-test",
                {"ean": "invalid", "price": "10", "stock": "1",
                 "condition": "NEW", "delivery_code": "3-5d"},
            )

        assert result["success"] is False
        assert "EAN is invalid" in result["error"]


# ── Endpoint integration ─────────────────────────────────────────────

class TestBolPushEndpoint:

    def test_push_requires_auth(self, client):
        """WHY: bol-push modifies seller data — must require JWT."""
        resp = client.post("/api/converter/bol-push", json={"offers": [{"ean": "123"}]})
        assert resp.status_code == 401

    def test_push_validates_empty_offers(self, auth_client):
        resp = auth_client.post("/api/converter/bol-push", json={"offers": []})
        assert resp.status_code == 422

    def test_push_validates_missing_ean(self, auth_client):
        resp = auth_client.post("/api/converter/bol-push", json={"offers": [{"title": "X"}]})
        assert resp.status_code == 422

    def test_push_validates_max_50(self, auth_client):
        offers = [{"ean": f"ean-{i}"} for i in range(51)]
        resp = auth_client.post("/api/converter/bol-push", json={"offers": offers})
        assert resp.status_code == 422
