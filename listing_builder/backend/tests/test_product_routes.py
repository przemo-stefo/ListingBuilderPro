# backend/tests/test_product_routes.py
# Purpose: Product CRUD route HTTP tests
# NOT for: Import or AI optimization

import pytest
from models.product import Product, ProductStatus


def _seed_product(db_session, source_id="prod-1", title="Test Product"):
    """Insert a product directly for route tests."""
    p = Product(
        source_platform="allegro",
        source_id=source_id,
        title_original=title,
        status=ProductStatus.IMPORTED,
        currency="PLN",
        images=[],
        attributes={},
        marketplace_data={},
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


class TestListProducts:

    def test_list_empty(self, client, test_settings):
        resp = client.get(
            "/api/products",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_products(self, client, test_settings, db_session):
        _seed_product(db_session, "p1", "Product One")
        _seed_product(db_session, "p2", "Product Two")
        resp = client.get(
            "/api/products",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_pagination(self, client, test_settings, db_session):
        for i in range(5):
            _seed_product(db_session, f"pg-{i}", f"Product {i}")
        resp = client.get(
            "/api/products?page=1&page_size=2",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3


class TestGetProduct:

    def test_get_existing(self, client, test_settings, db_session):
        p = _seed_product(db_session)
        resp = client.get(
            f"/api/products/{p.id}",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["source_id"] == "prod-1"

    def test_get_nonexistent_404(self, client, test_settings):
        resp = client.get(
            "/api/products/99999",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 404


class TestUpdateProduct:

    def test_update_title(self, client, test_settings, db_session):
        p = _seed_product(db_session)
        resp = client.put(
            f"/api/products/{p.id}",
            json={"title_original": "Updated Title"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["title_original"] == "Updated Title"

    def test_update_nonexistent_404(self, client, test_settings):
        resp = client.put(
            "/api/products/99999",
            json={"title_original": "Nope"},
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 404


class TestDeleteProduct:

    def test_delete_existing(self, client, test_settings, db_session):
        p = _seed_product(db_session)
        resp = client.delete(
            f"/api/products/{p.id}",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_nonexistent_404(self, client, test_settings):
        resp = client.delete(
            "/api/products/99999",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 404


class TestDashboardStats:

    def test_stats_empty_db(self, client, test_settings):
        resp = client.get(
            "/api/products/stats/summary",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 0

    def test_stats_with_products(self, client, test_settings, db_session):
        _seed_product(db_session, "s1")
        _seed_product(db_session, "s2")
        resp = client.get(
            "/api/products/stats/summary",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        data = resp.json()
        assert data["total_products"] == 2
        assert data["pending_optimization"] == 2
