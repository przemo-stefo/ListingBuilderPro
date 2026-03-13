# backend/tests/test_stress_multiuser.py
# Purpose: Stress test — 50 users on key endpoints, multi-tenant isolation
# NOT for: Unit tests or integration tests (those are in other files)

import pytest
from typing import Dict
from unittest.mock import patch, AsyncMock

from tests.conftest import create_user_settings_table

API_KEY_HEADER = "X-API-Key"
API_KEY_VALUE = "test-secret-key-minimum-16"

_HEADERS: Dict[str, str] = {API_KEY_HEADER: API_KEY_VALUE}


def _set_all_limiters(enabled: bool) -> None:
    """Toggle ALL slowapi Limiter instances across route modules.

    WHY: Each route file creates its own Limiter — disabling main.limiter alone
    doesn't affect per-route limiters. Must toggle all individually.
    """
    import api.import_routes, api.optimizer_routes, api.converter_routes
    import api.product_routes, api.settings_routes, api.oauth_routes, main
    for mod in [main, api.import_routes, api.optimizer_routes, api.converter_routes,
                api.product_routes, api.settings_routes, api.oauth_routes]:
        if hasattr(mod, "limiter"):
            mod.limiter.enabled = enabled


@pytest.fixture(autouse=True, scope="module")
def _no_rate_limits():
    """WHY: Stress tests fire 50+ requests instantly — rate limiter would reject most.
    Production limits are tested in test_user_journeys; here we test stability."""
    _set_all_limiters(False)
    yield
    _set_all_limiters(True)


MOCK_OPTIMIZER_RESULT: Dict = {
    "status": "success", "marketplace": "amazon_de", "brand": "TestBrand",
    "mode": "aggressive", "language": "de",
    "listing": {
        "title": "Optimierter Titel",
        "bullet_points": ["B1", "B2", "B3", "B4", "B5"],
        "description": "Beschreibung", "backend_keywords": "kw1 kw2 kw3",
    },
    "scores": {
        "coverage_pct": 85, "coverage_mode": "aggressive",
        "exact_matches_in_title": 1, "title_coverage_pct": 90,
        "backend_utilization_pct": 60, "backend_byte_size": 200,
        "compliance_status": "PASS",
    },
    "compliance": {"status": "PASS", "issues": []},
    "keyword_intel": {
        "total_analyzed": 1, "tier1_title": 1, "tier2_bullets": 0,
        "tier3_backend": 0, "missing_keywords": [], "root_words": [],
    },
    "ranking_juice": {"score": 80, "grade": "B+", "verdict": "Good"},
    "llm_provider": "groq", "optimization_source": "direct",
}


class TestStress50Users:
    """Simulate 50 requests to core endpoints — verifies stability."""

    def test_50_health_checks(self, client):
        for i in range(50):
            resp = client.get("/health")
            assert resp.status_code == 200, f"Request {i}: {resp.status_code}"

    def test_50_marketplaces_requests(self, auth_client):
        for i in range(50):
            resp = auth_client.get("/api/converter/marketplaces", headers=_HEADERS)
            assert resp.status_code == 200, f"Request {i}: {resp.status_code}"
            assert len(resp.json()["marketplaces"]) >= 5

    def test_50_settings_reads(self, auth_client, db_session):
        create_user_settings_table(db_session)
        for i in range(50):
            resp = auth_client.get("/api/settings", headers=_HEADERS)
            assert resp.status_code == 200, f"Request {i}: {resp.status_code}"

    def test_50_oauth_connections_reads(self, auth_client):
        for i in range(50):
            resp = auth_client.get("/api/oauth/connections", headers=_HEADERS)
            assert resp.status_code == 200, f"Request {i}: {resp.status_code}"

    def test_50_product_imports(self, auth_client):
        for i in range(50):
            resp = auth_client.post("/api/import/product", json={
                "source_id": f"stress-{i}",
                "title": f"Stress Test Product {i}",
                "source_platform": "allegro",
            }, headers=_HEADERS)
            assert resp.status_code == 200, f"Import {i}: {resp.status_code} {resp.text[:100]}"

        resp = auth_client.get("/api/products?page_size=100", headers=_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json().get("items", [])) >= 50

    @patch("api.optimizer_routes._check_tier_limit")
    @patch("api.optimizer_routes.optimize_listing", new_callable=AsyncMock)
    def test_50_optimizer_generates(self, mock_gen, mock_tier, auth_client):
        """50 optimizer generate calls — the MOST critical endpoint."""
        mock_gen.return_value = MOCK_OPTIMIZER_RESULT
        for i in range(50):
            resp = auth_client.post("/api/optimizer/generate", json={
                "product_title": f"Buty sportowe Nike Air Max {i}",
                "brand": "Nike",
                "keywords": [{"phrase": "buty sportowe", "search_volume": 5000}],
                "marketplace": "amazon_de",
                "mode": "aggressive",
            }, headers=_HEADERS)
            assert resp.status_code == 200, f"Generate {i}: {resp.status_code} {resp.text[:200]}"
        assert mock_gen.call_count == 50


class TestMultiTenantIsolation:
    """Verify user A cannot see user B's data — critical for Mateusz.

    WHY dynamic_auth_client: Creates ONE TestClient with switchable user identity.
    Previous approach created 50+ TestClient instances (~100ms each = 5s overhead).
    Now: single client, user switch = just changing a mutable list. ~10x faster.
    """

    def test_two_users_product_isolation(self, dynamic_auth_client):
        """User A imports 10 products, User B must NOT see them."""
        client, switch_user = dynamic_auth_client

        switch_user("isolation-user-A-0001", "usera@test.com")
        for i in range(10):
            resp = client.post("/api/import/product", json={
                "source_id": f"a-{i}", "title": f"User A Product {i}",
                "source_platform": "allegro",
            }, headers=_HEADERS)
            assert resp.status_code == 200, f"User A import {i}: {resp.status_code}"

        resp_a = client.get("/api/products?page_size=100", headers=_HEADERS)
        assert resp_a.status_code == 200
        assert len(resp_a.json().get("items", [])) == 10

        switch_user("isolation-user-B-0002", "userb@test.com")
        resp_b = client.get("/api/products?page_size=100", headers=_HEADERS)
        assert resp_b.status_code == 200
        items_b = resp_b.json().get("items", [])
        assert len(items_b) == 0, f"ISOLATION BREACH! User B sees {len(items_b)} products"

    def test_50_unique_users_all_isolated(self, dynamic_auth_client):
        """50 unique users — each imports 1 product, each sees only their own."""
        client, switch_user = dynamic_auth_client

        for i in range(50):
            switch_user(f"iso-user-{i:04d}", f"iso{i}@test.com")

            resp = client.post("/api/import/product", json={
                "source_id": f"iso-{i}", "title": f"Product by user {i}",
                "source_platform": "allegro",
            }, headers=_HEADERS)
            assert resp.status_code == 200, f"User {i}: {resp.text[:100]}"

            products = client.get("/api/products?page_size=100", headers=_HEADERS).json().get("items", [])
            assert len(products) == 1, f"User {i} sees {len(products)} — ISOLATION BREACH!"
