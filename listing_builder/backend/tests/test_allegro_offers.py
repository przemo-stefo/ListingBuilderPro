# backend/tests/test_allegro_offers.py
# Purpose: Tests for Allegro Offers Manager — validation, endpoints, edge cases
# NOT for: Integration tests with real Allegro API

import re
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.allegro_offers_routes import (
    router,
    OFFER_ID_PATTERN,
    OfferManagerUpdateRequest,
    BulkStatusRequest,
    BulkPriceChange,
    BulkPriceRequest,
    OfferPriceUpdate,
)
from pydantic import ValidationError


# --- FastAPI test app ---

app = FastAPI()
app.include_router(router)


# WHY: Mock get_db so we don't need a real database connection
def mock_get_db():
    return MagicMock()


app.dependency_overrides = {}


# --- Pydantic Model Validation Tests ---

class TestOfferIdPattern:
    """Validate the offer ID regex pattern."""

    def test_valid_8_digits(self):
        assert OFFER_ID_PATTERN.match("12345678")

    def test_valid_14_digits(self):
        assert OFFER_ID_PATTERN.match("12345678901234")

    def test_valid_10_digits(self):
        assert OFFER_ID_PATTERN.match("1234567890")

    def test_reject_7_digits(self):
        assert not OFFER_ID_PATTERN.match("1234567")

    def test_reject_15_digits(self):
        assert not OFFER_ID_PATTERN.match("123456789012345")

    def test_reject_letters(self):
        assert not OFFER_ID_PATTERN.match("abcdefgh")

    def test_reject_mixed(self):
        assert not OFFER_ID_PATTERN.match("1234abcd")

    def test_reject_empty(self):
        assert not OFFER_ID_PATTERN.match("")

    def test_reject_path_traversal(self):
        assert not OFFER_ID_PATTERN.match("../../etc")

    def test_reject_special_chars(self):
        assert not OFFER_ID_PATTERN.match("12345678;DROP")


class TestOfferPriceUpdate:
    """Validate price field format."""

    def test_valid_integer_price(self):
        p = OfferPriceUpdate(amount="199")
        assert p.amount == "199"

    def test_valid_decimal_price(self):
        p = OfferPriceUpdate(amount="49.99")
        assert p.amount == "49.99"

    def test_valid_one_decimal(self):
        p = OfferPriceUpdate(amount="10.5")
        assert p.amount == "10.5"

    def test_reject_negative(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="-10")

    def test_reject_letters(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="abc")

    def test_reject_three_decimals(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="10.999")

    def test_reject_empty(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="")

    def test_default_currency_pln(self):
        p = OfferPriceUpdate(amount="10")
        assert p.currency == "PLN"

    def test_valid_eur_currency(self):
        p = OfferPriceUpdate(amount="10", currency="EUR")
        assert p.currency == "EUR"

    def test_reject_invalid_currency(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="10", currency="XYZ")

    def test_reject_lowercase_currency(self):
        with pytest.raises(ValidationError):
            OfferPriceUpdate(amount="10", currency="pln")


class TestOfferManagerUpdateRequest:
    """Validate partial update request."""

    def test_name_only(self):
        r = OfferManagerUpdateRequest(name="Test product")
        assert r.name == "Test product"
        assert r.price is None
        assert r.description_html is None

    def test_price_only(self):
        r = OfferManagerUpdateRequest(price=OfferPriceUpdate(amount="29.99"))
        assert r.name is None
        assert r.price.amount == "29.99"

    def test_name_max_length_75(self):
        r = OfferManagerUpdateRequest(name="A" * 75)
        assert len(r.name) == 75

    def test_reject_name_over_75(self):
        with pytest.raises(ValidationError):
            OfferManagerUpdateRequest(name="A" * 76)

    def test_reject_empty_name(self):
        with pytest.raises(ValidationError):
            OfferManagerUpdateRequest(name="")

    def test_description_max_length(self):
        r = OfferManagerUpdateRequest(description_html="<p>Test</p>")
        assert r.description_html == "<p>Test</p>"

    def test_reject_description_over_50000(self):
        with pytest.raises(ValidationError):
            OfferManagerUpdateRequest(description_html="x" * 50001)

    def test_all_fields_none_valid(self):
        # WHY: all None is valid at Pydantic level — endpoint rejects it with 400
        r = OfferManagerUpdateRequest()
        assert r.name is None


class TestBulkStatusRequest:
    """Validate bulk status change request."""

    def test_valid_activate(self):
        r = BulkStatusRequest(offer_ids=["12345678"], action="ACTIVATE")
        assert r.action == "ACTIVATE"

    def test_valid_end(self):
        r = BulkStatusRequest(offer_ids=["12345678"], action="END")
        assert r.action == "END"

    def test_reject_invalid_action(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(offer_ids=["12345678"], action="PAUSE")

    def test_reject_empty_list(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(offer_ids=[], action="ACTIVATE")

    def test_reject_invalid_offer_id(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(offer_ids=["abc"], action="ACTIVATE")

    def test_reject_empty_string_offer_id(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(offer_ids=[""], action="ACTIVATE")

    def test_reject_path_traversal_in_bulk(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(offer_ids=["../../etc/passwd"], action="ACTIVATE")

    def test_multiple_valid_ids(self):
        r = BulkStatusRequest(
            offer_ids=["12345678", "87654321", "1234567890"],
            action="ACTIVATE"
        )
        assert len(r.offer_ids) == 3

    def test_mixed_valid_invalid_ids(self):
        with pytest.raises(ValidationError):
            BulkStatusRequest(
                offer_ids=["12345678", "bad_id", "87654321"],
                action="ACTIVATE"
            )


class TestBulkPriceChange:
    """Validate single price change item."""

    def test_valid(self):
        c = BulkPriceChange(offer_id="12345678", price="49.99")
        assert c.offer_id == "12345678"
        assert c.price == "49.99"
        assert c.currency == "PLN"

    def test_reject_invalid_offer_id(self):
        with pytest.raises(ValidationError):
            BulkPriceChange(offer_id="abc", price="10")

    def test_reject_invalid_price(self):
        with pytest.raises(ValidationError):
            BulkPriceChange(offer_id="12345678", price="free")

    def test_reject_negative_price(self):
        with pytest.raises(ValidationError):
            BulkPriceChange(offer_id="12345678", price="-5")


class TestBulkPriceRequest:
    """Validate bulk price change request."""

    def test_valid_single(self):
        r = BulkPriceRequest(changes=[
            BulkPriceChange(offer_id="12345678", price="29.99")
        ])
        assert len(r.changes) == 1

    def test_reject_empty(self):
        with pytest.raises(ValidationError):
            BulkPriceRequest(changes=[])

    def test_multiple_changes(self):
        r = BulkPriceRequest(changes=[
            BulkPriceChange(offer_id="12345678", price="29.99"),
            BulkPriceChange(offer_id="87654321", price="39.99", currency="EUR"),
        ])
        assert len(r.changes) == 2


# --- Helper Function Tests ---

class TestExtractAllegroError:
    """Test error extraction from Allegro API responses."""

    def test_extracts_error_message(self):
        from api.allegro_offers_routes import _extract_allegro_error

        resp = MagicMock()
        resp.json.return_value = {
            "errors": [{"message": "Offer not found", "code": "NOT_FOUND"}]
        }
        resp.text = "raw text"
        assert _extract_allegro_error(resp) == "Offer not found"

    def test_empty_errors_list(self):
        from api.allegro_offers_routes import _extract_allegro_error

        resp = MagicMock()
        resp.json.return_value = {"errors": []}
        resp.text = "something went wrong"
        assert _extract_allegro_error(resp) == "something went wrong"

    def test_no_errors_key(self):
        from api.allegro_offers_routes import _extract_allegro_error

        resp = MagicMock()
        resp.json.return_value = {"status": "error"}
        resp.text = "server error"
        assert _extract_allegro_error(resp) == "server error"

    def test_html_response(self):
        from api.allegro_offers_routes import _extract_allegro_error

        resp = MagicMock()
        resp.json.side_effect = ValueError("not JSON")
        resp.text = "<html><body>502 Bad Gateway</body></html>"
        result = _extract_allegro_error(resp)
        assert "502 Bad Gateway" in result

    def test_truncates_long_text(self):
        from api.allegro_offers_routes import _extract_allegro_error

        resp = MagicMock()
        resp.json.side_effect = ValueError("not JSON")
        resp.text = "x" * 500
        result = _extract_allegro_error(resp)
        assert len(result) == 200


# --- Endpoint Tests (with mocked Allegro API) ---

client = TestClient(app)


class TestListOffersEndpoint:
    """Test GET /api/allegro/offers."""

    @patch("api.allegro_offers_routes.get_access_token")
    @patch("api.allegro_offers_routes.httpx.AsyncClient")
    def test_list_offers_success(self, mock_client_cls, mock_token):
        mock_token.return_value = "test_token"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "offers": [
                {
                    "id": "12345678",
                    "name": "Test Offer",
                    "sellingMode": {"price": {"amount": "49.99", "currency": "PLN"}},
                    "stock": {"available": 10},
                    "publication": {"status": "ACTIVE"},
                    "primaryImage": {"url": "https://img.allegro.pl/test.jpg"},
                    "category": {"id": "123"},
                }
            ],
            "totalCount": 1,
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        response = client.get("/api/allegro/offers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["offers"]) == 1
        assert data["offers"][0]["id"] == "12345678"
        assert data["offers"][0]["name"] == "Test Offer"
        assert data["offers"][0]["price"]["amount"] == "49.99"

    @patch("api.allegro_offers_routes.get_access_token")
    def test_list_offers_no_token(self, mock_token):
        mock_token.return_value = None
        response = client.get("/api/allegro/offers")
        assert response.status_code == 400
        assert "połączone" in response.json()["detail"].lower()

    def test_list_offers_invalid_limit(self):
        """limit=0 should be rejected by Query(ge=1)."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.get("/api/allegro/offers?limit=0")
            assert response.status_code == 422

    def test_list_offers_negative_offset(self):
        """offset=-1 should be rejected by Query(ge=0)."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.get("/api/allegro/offers?offset=-1")
            assert response.status_code == 422

    def test_list_offers_invalid_status(self):
        """Invalid status should be rejected by Literal."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.get("/api/allegro/offers?status=PAUSED")
            assert response.status_code == 422

    def test_list_offers_search_too_long(self):
        """Search over 100 chars should be rejected."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.get(f"/api/allegro/offers?search={'x' * 101}")
            assert response.status_code == 422


class TestGetOfferDetailEndpoint:
    """Test GET /api/allegro/offers/{offer_id}."""

    @patch("api.allegro_offers_routes.get_access_token")
    @patch("api.allegro_offers_routes.fetch_offer_details")
    def test_get_detail_success(self, mock_fetch, mock_token):
        mock_token.return_value = "test_token"
        mock_fetch.return_value = {
            "source_url": "https://allegro.pl/oferta/12345678",
            "title": "Test",
            "price": "49.99",
            "error": None,
        }

        response = client.get("/api/allegro/offers/12345678")
        assert response.status_code == 200
        assert response.json()["title"] == "Test"

    @patch("api.allegro_offers_routes.get_access_token")
    def test_get_detail_invalid_id(self, mock_token):
        mock_token.return_value = "test_token"
        response = client.get("/api/allegro/offers/abc")
        assert response.status_code == 400
        assert "cyfr" in response.json()["detail"]

    @patch("api.allegro_offers_routes.get_access_token")
    def test_get_detail_path_traversal(self, mock_token):
        mock_token.return_value = "test_token"
        response = client.get("/api/allegro/offers/../../etc")
        # FastAPI won't match this route due to path format
        assert response.status_code in (400, 404, 422)


class TestUpdateOfferEndpoint:
    """Test PATCH /api/allegro/offers/{offer_id}."""

    @patch("api.allegro_offers_routes.get_access_token")
    @patch("api.allegro_offers_routes.httpx.AsyncClient")
    def test_update_name_success(self, mock_client_cls, mock_token):
        mock_token.return_value = "test_token"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.patch.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        response = client.patch(
            "/api/allegro/offers/12345678",
            json={"name": "New Title"}
        )
        assert response.status_code == 200

    def test_update_empty_body(self):
        """All fields None = 400."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.patch("/api/allegro/offers/12345678", json={})
            assert response.status_code == 400
            assert "Brak" in response.json()["detail"]

    def test_update_invalid_id(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.patch("/api/allegro/offers/bad", json={"name": "X"})
            assert response.status_code == 400

    def test_update_name_too_long(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.patch(
                "/api/allegro/offers/12345678",
                json={"name": "A" * 76}
            )
            assert response.status_code == 422

    def test_update_invalid_price_format(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.patch(
                "/api/allegro/offers/12345678",
                json={"price": {"amount": "free", "currency": "PLN"}}
            )
            assert response.status_code == 422


class TestBulkStatusEndpoint:
    """Test POST /api/allegro/offers/bulk-status."""

    @patch("api.allegro_offers_routes.get_access_token")
    @patch("api.allegro_offers_routes.httpx.AsyncClient")
    def test_bulk_activate_success(self, mock_client_cls, mock_token):
        mock_token.return_value = "test_token"

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        response = client.post(
            "/api/allegro/offers/bulk-status",
            json={"offer_ids": ["12345678", "87654321"], "action": "ACTIVATE"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["count"] == 2
        assert "command_id" in data

    def test_bulk_invalid_action(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-status",
                json={"offer_ids": ["12345678"], "action": "PAUSE"}
            )
            assert response.status_code == 422

    def test_bulk_empty_ids(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-status",
                json={"offer_ids": [], "action": "ACTIVATE"}
            )
            assert response.status_code == 422

    def test_bulk_invalid_offer_id(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-status",
                json={"offer_ids": ["bad_id"], "action": "ACTIVATE"}
            )
            assert response.status_code == 422

    def test_bulk_injection_attempt(self):
        """Offer IDs that look like SQL injection should be rejected."""
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-status",
                json={"offer_ids": ["1; DROP TABLE"], "action": "END"}
            )
            assert response.status_code == 422


class TestBulkPriceEndpoint:
    """Test POST /api/allegro/offers/bulk-price."""

    @patch("api.allegro_offers_routes.get_access_token")
    @patch("api.allegro_offers_routes.httpx.AsyncClient")
    def test_bulk_price_success(self, mock_client_cls, mock_token):
        mock_token.return_value = "test_token"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        response = client.post(
            "/api/allegro/offers/bulk-price",
            json={"changes": [
                {"offer_id": "12345678", "price": "49.99", "currency": "PLN"},
                {"offer_id": "87654321", "price": "29.99"},
            ]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_bulk_price_empty_changes(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-price",
                json={"changes": []}
            )
            assert response.status_code == 422

    def test_bulk_price_invalid_amount(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-price",
                json={"changes": [
                    {"offer_id": "12345678", "price": "free"}
                ]}
            )
            assert response.status_code == 422

    def test_bulk_price_invalid_offer_id(self):
        with patch("api.allegro_offers_routes.get_access_token", return_value="token"):
            response = client.post(
                "/api/allegro/offers/bulk-price",
                json={"changes": [
                    {"offer_id": "hack", "price": "10"}
                ]}
            )
            assert response.status_code == 422
