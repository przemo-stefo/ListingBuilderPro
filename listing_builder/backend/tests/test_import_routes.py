# backend/tests/test_import_routes.py
# Purpose: Import route HTTP tests — webhook, single, batch endpoints
# NOT for: Service-level DB logic

import pytest
from unittest.mock import patch


class TestWebhookEndpoint:

    def test_webhook_no_secret_returns_401(self, client):
        resp = client.post("/api/import/webhook", json={
            "source": "allegro",
            "event_type": "product.import",
            "data": {"products": []},
        })
        assert resp.status_code == 401

    def test_webhook_bad_secret_returns_401(self, client):
        resp = client.post(
            "/api/import/webhook",
            json={
                "source": "allegro",
                "event_type": "product.import",
                "data": {"products": []},
            },
            headers={"X-Webhook-Secret": "wrong-secret"},
        )
        assert resp.status_code == 401

    def test_webhook_valid_secret_empty_products_returns_400(self, client, test_settings):
        resp = client.post(
            "/api/import/webhook",
            json={
                "source": "allegro",
                "data": {"products": []},
            },
            headers={"X-Webhook-Secret": test_settings.webhook_secret},
        )
        assert resp.status_code == 400

    def test_webhook_valid_import(self, client, test_settings):
        resp = client.post(
            "/api/import/webhook",
            json={
                "source": "allegro",
                "data": {
                    "products": [{
                        "source_id": "wh-001",
                        "title": "Webhook Product",
                        "source_platform": "allegro",
                    }]
                },
            },
            headers={"X-Webhook-Secret": test_settings.webhook_secret},
        )
        assert resp.status_code == 200
        assert resp.json()["success_count"] == 1


class TestSingleProductImport:

    def test_import_product_no_auth_401(self, client):
        resp = client.post("/api/import/product", json={
            "source_id": "p-001",
            "title": "Test",
        })
        assert resp.status_code == 401

    def test_import_product_success(self, client, test_settings):
        resp = client.post(
            "/api/import/product",
            json={
                "source_id": "p-002",
                "title": "Single Import Product",
                "source_platform": "allegro",
            },
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestBatchImport:

    def test_batch_empty_returns_400(self, client, test_settings):
        resp = client.post(
            "/api/import/batch",
            json=[],
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 400

    def test_batch_success(self, client, test_settings):
        products = [
            {"source_id": f"b-{i}", "title": f"Batch {i}", "source_platform": "allegro"}
            for i in range(3)
        ]
        resp = client.post(
            "/api/import/batch",
            json=products,
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        assert resp.json()["success_count"] == 3


class TestJobStatus:

    def test_nonexistent_job_404(self, client, test_settings):
        resp = client.get(
            "/api/import/job/99999",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 404
