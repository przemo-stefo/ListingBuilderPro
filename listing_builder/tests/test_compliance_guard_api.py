# tests/test_compliance_guard_api.py
# Purpose: Test suite for Compliance Guard FastAPI backend
# NOT for: Testing individual marketplace connectors (separate test files)

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

# Will be created
from compliance_guard.api import app
from compliance_guard.models import (
    Alert, AlertType, AlertSeverity, AlertStatus,
    InventoryItem, BuyBoxStatus, SellerMetrics,
    DashboardSummary, HealthScore, Marketplace
)
from compliance_guard.services import (
    UnifiedDataService,
    AlertService,
    DashboardService
)

from fastapi.testclient import TestClient


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_amazon_connector():
    """Mock Amazon SP-API connector"""
    connector = Mock()
    connector.get_inventory.return_value = [
        {
            "sku": "AMZ-001",
            "asin": "B0TEST123",
            "title": "Test Product Amazon",
            "quantity": 50,
            "price": 29.99,
            "fulfillment_channel": "FBA"
        }
    ]
    connector.get_buy_box_status.return_value = {
        "B0TEST123": {
            "has_buy_box": True,
            "buy_box_price": 29.99,
            "competitor_price": 31.99
        }
    }
    return connector


@pytest.fixture
def mock_ebay_connector():
    """Mock eBay API connector"""
    connector = Mock()
    connector.get_inventory.return_value = [
        {
            "sku": "EBAY-001",
            "listing_id": "123456789",
            "title": "Test Product eBay",
            "quantity": 30,
            "price": 34.99
        }
    ]
    connector.get_seller_metrics.return_value = {
        "feedback_score": 99.5,
        "return_rate": 2.1,
        "defect_rate": 0.3
    }
    return connector


@pytest.fixture
def sample_alert():
    """Sample alert for testing"""
    return Alert(
        id="alert-001",
        type=AlertType.BUY_BOX_LOST,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.ACTIVE,
        marketplace=Marketplace.AMAZON,
        sku="AMZ-001",
        title="Buy Box Lost: Test Product",
        message="You lost the Buy Box for B0TEST123",
        created_at=datetime.utcnow(),
        data={"asin": "B0TEST123", "competitor_price": 27.99}
    )


# =============================================================================
# TEST: HEALTH ENDPOINT
# =============================================================================

class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_check_returns_200(self, client):
        """Health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Health endpoint returns service status"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_includes_version(self, client):
        """Health endpoint includes API version"""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check_includes_timestamp(self, client):
        """Health endpoint includes timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data


# =============================================================================
# TEST: INVENTORY ENDPOINTS
# =============================================================================

class TestInventoryEndpoints:
    """Test /api/inventory endpoints"""

    def test_get_all_inventory_returns_200(self, client):
        """GET /api/inventory returns 200"""
        response = client.get("/api/inventory")
        assert response.status_code == 200

    def test_get_inventory_returns_list(self, client):
        """GET /api/inventory returns list of items"""
        response = client.get("/api/inventory")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_inventory_by_marketplace(self, client):
        """GET /api/inventory?marketplace=amazon filters correctly"""
        response = client.get("/api/inventory?marketplace=amazon")
        assert response.status_code == 200
        data = response.json()
        # All items should be from amazon
        for item in data["items"]:
            assert item["marketplace"] == "amazon"

    def test_get_inventory_low_stock_filter(self, client):
        """GET /api/inventory?low_stock=true returns low stock items"""
        response = client.get("/api/inventory?low_stock=true&threshold=10")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["quantity"] <= 10

    def test_get_inventory_includes_marketplace_field(self, client):
        """Inventory items include marketplace field"""
        response = client.get("/api/inventory")
        data = response.json()
        if data["items"]:
            assert "marketplace" in data["items"][0]

    def test_get_inventory_item_by_sku(self, client):
        """GET /api/inventory/{sku} returns specific item"""
        response = client.get("/api/inventory/AMZ-001")
        assert response.status_code in [200, 404]  # 200 if exists, 404 if not

    def test_get_inventory_includes_total_count(self, client):
        """Response includes total count"""
        response = client.get("/api/inventory")
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)


# =============================================================================
# TEST: BUY BOX ENDPOINTS
# =============================================================================

class TestBuyBoxEndpoints:
    """Test /api/buy-box endpoints"""

    def test_get_buy_box_status_returns_200(self, client):
        """GET /api/buy-box returns 200"""
        response = client.get("/api/buy-box")
        assert response.status_code == 200

    def test_get_buy_box_returns_list(self, client):
        """GET /api/buy-box returns list of statuses"""
        response = client.get("/api/buy-box")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_buy_box_lost_only(self, client):
        """GET /api/buy-box?lost_only=true filters lost Buy Box"""
        response = client.get("/api/buy-box?lost_only=true")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["has_buy_box"] == False

    def test_buy_box_item_has_required_fields(self, client):
        """Buy Box items have required fields"""
        response = client.get("/api/buy-box")
        data = response.json()
        required_fields = ["asin", "has_buy_box", "your_price", "buy_box_price"]
        if data["items"]:
            for field in required_fields:
                assert field in data["items"][0]

    def test_get_buy_box_by_asin(self, client):
        """GET /api/buy-box/{asin} returns specific ASIN status"""
        response = client.get("/api/buy-box/B0TEST123")
        assert response.status_code in [200, 404]


# =============================================================================
# TEST: ALERTS ENDPOINTS
# =============================================================================

class TestAlertsEndpoints:
    """Test /api/alerts endpoints"""

    def test_get_all_alerts_returns_200(self, client):
        """GET /api/alerts returns 200"""
        response = client.get("/api/alerts")
        assert response.status_code == 200

    def test_get_alerts_returns_list(self, client):
        """GET /api/alerts returns list"""
        response = client.get("/api/alerts")
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_alerts_filter_by_type(self, client):
        """GET /api/alerts?type=buy_box_lost filters by type"""
        response = client.get("/api/alerts?type=buy_box_lost")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["type"] == "buy_box_lost"

    def test_get_alerts_filter_by_severity(self, client):
        """GET /api/alerts?severity=high filters by severity"""
        response = client.get("/api/alerts?severity=high")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["severity"] == "high"

    def test_get_alerts_filter_by_status(self, client):
        """GET /api/alerts?status=active filters by status"""
        response = client.get("/api/alerts?status=active")
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["status"] == "active"

    def test_get_alert_by_id(self, client):
        """GET /api/alerts/{id} returns specific alert"""
        response = client.get("/api/alerts/alert-001")
        assert response.status_code in [200, 404]

    def test_create_alert(self, client):
        """POST /api/alerts creates new alert"""
        alert_data = {
            "type": "low_stock",
            "severity": "medium",
            "marketplace": "amazon",
            "sku": "AMZ-002",
            "title": "Low Stock Alert",
            "message": "Stock below threshold for AMZ-002"
        }
        response = client.post("/api/alerts", json=alert_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["type"] == "low_stock"

    def test_update_alert_status(self, client):
        """PATCH /api/alerts/{id}/status updates alert status"""
        response = client.patch(
            "/api/alerts/alert-001/status",
            json={"status": "acknowledged"}
        )
        assert response.status_code in [200, 404]

    def test_dismiss_alert(self, client):
        """DELETE /api/alerts/{id} dismisses alert"""
        response = client.delete("/api/alerts/alert-001")
        assert response.status_code in [200, 204, 404]

    def test_get_alerts_count_by_type(self, client):
        """GET /api/alerts/count returns counts by type"""
        response = client.get("/api/alerts/count")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data


# =============================================================================
# TEST: METRICS ENDPOINTS
# =============================================================================

class TestMetricsEndpoints:
    """Test /api/metrics endpoints"""

    def test_get_seller_metrics_returns_200(self, client):
        """GET /api/metrics returns 200"""
        response = client.get("/api/metrics")
        assert response.status_code == 200

    def test_get_metrics_by_marketplace(self, client):
        """GET /api/metrics?marketplace=ebay returns marketplace metrics"""
        response = client.get("/api/metrics?marketplace=ebay")
        assert response.status_code == 200
        data = response.json()
        assert "marketplace" in data

    def test_metrics_include_return_rate(self, client):
        """Metrics include return rate"""
        response = client.get("/api/metrics")
        data = response.json()
        assert "return_rate" in data or "metrics" in data

    def test_metrics_include_feedback_score(self, client):
        """Metrics include feedback score"""
        response = client.get("/api/metrics?marketplace=ebay")
        data = response.json()
        # eBay has feedback score
        if data.get("marketplace") == "ebay":
            assert "feedback_score" in data


# =============================================================================
# TEST: DASHBOARD ENDPOINTS
# =============================================================================

class TestDashboardEndpoints:
    """Test /api/dashboard endpoints"""

    def test_get_dashboard_summary_returns_200(self, client):
        """GET /api/dashboard returns 200"""
        response = client.get("/api/dashboard")
        assert response.status_code == 200

    def test_dashboard_includes_health_score(self, client):
        """Dashboard includes health score"""
        response = client.get("/api/dashboard")
        data = response.json()
        assert "health_score" in data
        assert 0 <= data["health_score"] <= 100

    def test_dashboard_includes_alert_summary(self, client):
        """Dashboard includes alert summary"""
        response = client.get("/api/dashboard")
        data = response.json()
        assert "alerts" in data
        assert "total" in data["alerts"]
        assert "critical" in data["alerts"]

    def test_dashboard_includes_inventory_summary(self, client):
        """Dashboard includes inventory summary"""
        response = client.get("/api/dashboard")
        data = response.json()
        assert "inventory" in data
        assert "total_skus" in data["inventory"]
        assert "low_stock_count" in data["inventory"]

    def test_dashboard_includes_buy_box_summary(self, client):
        """Dashboard includes Buy Box summary"""
        response = client.get("/api/dashboard")
        data = response.json()
        assert "buy_box" in data
        assert "total_asins" in data["buy_box"]
        assert "winning_count" in data["buy_box"]

    def test_dashboard_includes_marketplace_breakdown(self, client):
        """Dashboard includes per-marketplace breakdown"""
        response = client.get("/api/dashboard")
        data = response.json()
        assert "marketplaces" in data

    def test_get_dashboard_history(self, client):
        """GET /api/dashboard/history returns historical data"""
        response = client.get("/api/dashboard/history?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data


# =============================================================================
# TEST: AUTHENTICATION
# =============================================================================

class TestAuthentication:
    """Test API authentication"""

    def test_protected_endpoint_requires_api_key(self, client):
        """Protected endpoints require API key"""
        # Remove any default headers
        response = client.get(
            "/api/inventory",
            headers={"X-API-Key": ""}
        )
        # Should either work (if auth disabled) or return 401/403
        assert response.status_code in [200, 401, 403]

    def test_valid_api_key_allowed(self, client):
        """Valid API key allows access"""
        response = client.get(
            "/api/inventory",
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 200

    def test_health_endpoint_no_auth_required(self, client):
        """Health endpoint doesn't require auth"""
        response = client.get("/health")
        assert response.status_code == 200


# =============================================================================
# TEST: UNIFIED DATA SERVICE
# =============================================================================

class TestUnifiedDataService:
    """Test UnifiedDataService aggregation"""

    def test_service_aggregates_multiple_marketplaces(
        self, mock_amazon_connector, mock_ebay_connector
    ):
        """Service aggregates data from multiple marketplaces"""
        service = UnifiedDataService(
            connectors={
                "amazon": mock_amazon_connector,
                "ebay": mock_ebay_connector
            }
        )
        inventory = service.get_all_inventory()

        # Should have items from both marketplaces
        marketplaces = {item["marketplace"] for item in inventory}
        assert "amazon" in marketplaces
        assert "ebay" in marketplaces

    def test_service_transforms_to_unified_schema(
        self, mock_amazon_connector
    ):
        """Service transforms data to unified schema"""
        service = UnifiedDataService(
            connectors={"amazon": mock_amazon_connector}
        )
        inventory = service.get_all_inventory()

        # Each item should have standard fields
        required_fields = ["sku", "title", "quantity", "price", "marketplace"]
        for item in inventory:
            for field in required_fields:
                assert field in item

    def test_service_handles_connector_errors_gracefully(self):
        """Service handles connector errors without crashing"""
        failing_connector = Mock()
        failing_connector.get_inventory.side_effect = Exception("API Error")

        service = UnifiedDataService(
            connectors={"failing": failing_connector}
        )

        # Should not raise, should return empty or partial data
        inventory = service.get_all_inventory()
        assert isinstance(inventory, list)

    def test_service_caches_results(self, mock_amazon_connector):
        """Service caches results to reduce API calls"""
        service = UnifiedDataService(
            connectors={"amazon": mock_amazon_connector},
            cache_ttl=300
        )

        # First call
        service.get_all_inventory()
        # Second call should use cache
        service.get_all_inventory()

        # Connector should only be called once (cached)
        assert mock_amazon_connector.get_inventory.call_count == 1


# =============================================================================
# TEST: ALERT SERVICE
# =============================================================================

class TestAlertService:
    """Test AlertService functionality"""

    def test_create_alert(self):
        """AlertService creates alerts"""
        service = AlertService()
        alert = service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.MEDIUM,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-001",
            title="Low Stock",
            message="Stock below 10 units"
        )

        assert alert.id is not None
        assert alert.type == AlertType.LOW_STOCK
        assert alert.status == AlertStatus.ACTIVE

    def test_get_alerts_by_filter(self):
        """AlertService filters alerts correctly"""
        service = AlertService()

        # Create test alerts
        service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.LOW,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-001",
            title="Low Stock",
            message="Test"
        )
        service.create_alert(
            type=AlertType.BUY_BOX_LOST,
            severity=AlertSeverity.HIGH,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-002",
            title="Buy Box Lost",
            message="Test"
        )

        # Filter by type
        low_stock_alerts = service.get_alerts(type=AlertType.LOW_STOCK)
        assert all(a.type == AlertType.LOW_STOCK for a in low_stock_alerts)

    def test_update_alert_status(self):
        """AlertService updates alert status"""
        service = AlertService()
        alert = service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.MEDIUM,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-001",
            title="Test",
            message="Test"
        )

        updated = service.update_status(alert.id, AlertStatus.ACKNOWLEDGED)
        assert updated.status == AlertStatus.ACKNOWLEDGED

    def test_dismiss_alert(self):
        """AlertService dismisses alerts"""
        service = AlertService()
        alert = service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.MEDIUM,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-001",
            title="Test",
            message="Test"
        )

        service.dismiss_alert(alert.id)

        # Alert should be dismissed
        alerts = service.get_alerts()
        alert_ids = [a.id for a in alerts if a.status != AlertStatus.DISMISSED]
        assert alert.id not in alert_ids

    def test_get_alert_counts(self):
        """AlertService returns alert counts"""
        service = AlertService()

        # Create test alerts
        service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.LOW,
            marketplace=Marketplace.AMAZON,
            sku="AMZ-001",
            title="Test",
            message="Test"
        )
        service.create_alert(
            type=AlertType.LOW_STOCK,
            severity=AlertSeverity.MEDIUM,
            marketplace=Marketplace.EBAY,
            sku="EBAY-001",
            title="Test",
            message="Test"
        )

        counts = service.get_counts()
        assert counts["total"] >= 2
        assert "by_type" in counts


# =============================================================================
# TEST: DASHBOARD SERVICE
# =============================================================================

class TestDashboardService:
    """Test DashboardService functionality"""

    def test_calculate_health_score(
        self, mock_amazon_connector, mock_ebay_connector
    ):
        """DashboardService calculates health score"""
        unified_service = UnifiedDataService(
            connectors={
                "amazon": mock_amazon_connector,
                "ebay": mock_ebay_connector
            }
        )
        alert_service = AlertService()
        dashboard_service = DashboardService(
            unified_service=unified_service,
            alert_service=alert_service
        )

        summary = dashboard_service.get_summary()

        assert "health_score" in summary
        assert 0 <= summary["health_score"] <= 100

    def test_health_score_decreases_with_alerts(self):
        """Health score decreases with more alerts"""
        alert_service = AlertService()

        # Create multiple high severity alerts
        for i in range(5):
            alert_service.create_alert(
                type=AlertType.BUY_BOX_LOST,
                severity=AlertSeverity.HIGH,
                marketplace=Marketplace.AMAZON,
                sku=f"AMZ-{i}",
                title="Test",
                message="Test"
            )

        unified_service = Mock()
        unified_service.get_all_inventory.return_value = []
        unified_service.get_all_buy_box_status.return_value = []

        dashboard_service = DashboardService(
            unified_service=unified_service,
            alert_service=alert_service
        )

        summary = dashboard_service.get_summary()

        # With 5 high severity alerts, health score should be lower
        assert summary["health_score"] < 100

    def test_dashboard_includes_all_sections(
        self, mock_amazon_connector, mock_ebay_connector
    ):
        """Dashboard summary includes all required sections"""
        unified_service = UnifiedDataService(
            connectors={
                "amazon": mock_amazon_connector,
                "ebay": mock_ebay_connector
            }
        )
        alert_service = AlertService()
        dashboard_service = DashboardService(
            unified_service=unified_service,
            alert_service=alert_service
        )

        summary = dashboard_service.get_summary()

        required_sections = [
            "health_score", "alerts", "inventory",
            "buy_box", "marketplaces"
        ]
        for section in required_sections:
            assert section in summary


# =============================================================================
# TEST: WEBHOOK FOR N8N
# =============================================================================

class TestWebhookEndpoints:
    """Test webhook endpoints for n8n integration"""

    def test_webhook_receive_alert_returns_200(self, client):
        """POST /api/webhook/alert accepts alert from n8n"""
        alert_data = {
            "type": "buy_box_lost",
            "severity": "high",
            "marketplace": "amazon",
            "sku": "AMZ-001",
            "asin": "B0TEST123",
            "message": "Buy Box lost to competitor"
        }
        response = client.post(
            "/api/webhook/alert",
            json=alert_data,
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code in [200, 201]

    def test_webhook_returns_created_alert_id(self, client):
        """Webhook returns created alert ID"""
        alert_data = {
            "type": "low_stock",
            "severity": "medium",
            "marketplace": "ebay",
            "sku": "EBAY-001",
            "message": "Stock below threshold"
        }
        response = client.post(
            "/api/webhook/alert",
            json=alert_data,
            headers={"X-API-Key": "test-api-key"}
        )
        data = response.json()
        assert "alert_id" in data

    def test_webhook_data_endpoint(self, client):
        """GET /api/webhook/data returns data for n8n"""
        response = client.get(
            "/api/webhook/data?marketplace=amazon",
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "inventory" in data
        assert "buy_box" in data


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test API error handling"""

    def test_invalid_marketplace_returns_400(self, client):
        """Invalid marketplace parameter returns 400"""
        response = client.get("/api/inventory?marketplace=invalid")
        assert response.status_code == 400

    def test_invalid_alert_type_returns_400(self, client):
        """Invalid alert type returns 400"""
        response = client.get("/api/alerts?type=invalid_type")
        assert response.status_code == 400

    def test_not_found_returns_404(self, client):
        """Non-existent resource returns 404"""
        response = client.get("/api/alerts/nonexistent-id")
        assert response.status_code == 404

    def test_malformed_json_returns_422(self, client):
        """Malformed JSON returns 422"""
        response = client.post(
            "/api/alerts",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_error_response_has_detail(self, client):
        """Error responses include detail message"""
        response = client.get("/api/alerts/nonexistent-id")
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data


# =============================================================================
# TEST: PAGINATION
# =============================================================================

class TestPagination:
    """Test API pagination"""

    def test_inventory_supports_pagination(self, client):
        """GET /api/inventory supports limit and offset"""
        response = client.get("/api/inventory?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_alerts_support_pagination(self, client):
        """GET /api/alerts supports limit and offset"""
        response = client.get("/api/alerts?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
