# backend/tests/test_health.py
# Purpose: Health and root endpoint tests
# NOT for: Business logic

import pytest
from unittest.mock import patch


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_fields(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert "database" in data

    @patch("main.check_db_connection", return_value=True)
    def test_health_db_connected(self, mock_db, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    @patch("main.check_db_connection", return_value=False)
    def test_health_db_disconnected(self, mock_db, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"


class TestRootEndpoint:

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_response_shape(self, client):
        resp = client.get("/")
        data = resp.json()
        assert data["name"] == "Marketplace Listing Automation API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
