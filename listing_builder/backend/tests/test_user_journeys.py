# backend/tests/test_user_journeys.py
# Purpose: 20 end-to-end user journey tests simulating real user workflows
# NOT for: Unit tests of individual functions (those are in service-specific test files)

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import text
from models.product import Product, ProductStatus
from models.optimization import OptimizationRun
from models.monitoring import TrackedProduct, AlertConfig
from models.compliance import ComplianceReport
from tests.conftest import TEST_USER_ID, TEST_USER_EMAIL

API_KEY_HEADER = "X-API-Key"
API_KEY_VALUE = "test-secret-key-minimum-16"


def _headers(extra=None):
    """Standard auth headers (API key — JWT comes from auth_client fixture)."""
    h = {API_KEY_HEADER: API_KEY_VALUE}
    if extra:
        h.update(extra)
    return h


def _seed_product(db, source_id="prod-1", title="Test Product", status=ProductStatus.IMPORTED):
    """Insert a product owned by TEST_USER_ID."""
    p = Product(
        user_id=TEST_USER_ID,
        source_platform="allegro",
        source_id=source_id,
        title_original=title,
        status=status,
        currency="PLN",
        images=[],
        attributes={},
        marketplace_data={},
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _seed_optimization(db, title="Optimized Product", marketplace="amazon_de"):
    """Insert an optimization run owned by TEST_USER_ID."""
    run = OptimizationRun(
        user_id=TEST_USER_ID,
        product_title=title,
        brand="TestBrand",
        marketplace=marketplace,
        mode="full",
        request_data={"product_title": title, "brand": "TestBrand"},
        response_data={"title": "AI Title", "bullets": ["B1", "B2"]},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _create_user_settings_table(db):
    """Create user_settings table in SQLite (not a SQLAlchemy model — uses raw SQL)."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            settings TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()


def _create_listing_history_table(db):
    """Create listing_history table in SQLite for feedback tests."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS listing_history (
            id TEXT PRIMARY KEY,
            brand TEXT,
            marketplace TEXT,
            product_title TEXT,
            title TEXT,
            bullets TEXT,
            description TEXT,
            backend_keywords TEXT,
            ranking_juice REAL,
            grade TEXT,
            keyword_count INTEGER,
            user_rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()


# ── Journey 1: New user sees empty dashboard ──────────────────────────────────

class TestJ01EmptyDashboard:
    """New user with zero products sees empty stats."""

    def test_empty_dashboard_stats(self, auth_client, test_settings):
        resp = auth_client.get("/api/products/stats/summary", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 0
        assert data["pending_optimization"] == 0
        assert data["optimized_products"] == 0


# ── Journey 2: Import single product manually ─────────────────────────────────

class TestJ02ImportSingleProduct:
    """User imports one product via POST /api/import/product."""

    def test_import_single_product(self, auth_client, test_settings):
        resp = auth_client.post(
            "/api/import/product",
            json={
                "source_id": "manual-001",
                "title": "Reczne wprowadzenie produktu",
                "source_platform": "allegro",
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_imported_product_appears_in_list(self, auth_client, test_settings, db_session):
        _seed_product(db_session, "list-check", "Widoczny produkt")
        resp = auth_client.get("/api/products", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["source_id"] == "list-check"


# ── Journey 3: Import batch of products ───────────────────────────────────────

class TestJ03ImportBatch:
    """User imports 5 products at once via batch endpoint."""

    def test_batch_import_five_products(self, auth_client, test_settings):
        products = [
            {"source_id": f"batch-{i}", "title": f"Batch Product {i}", "source_platform": "allegro"}
            for i in range(5)
        ]
        resp = auth_client.post("/api/import/batch", json=products, headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["success_count"] == 5


# ── Journey 4: Product list with pagination and status filters ────────────────

class TestJ04ProductFilters:
    """User browses products with status filter + pagination."""

    def test_filter_by_status(self, auth_client, test_settings, db_session):
        _seed_product(db_session, "imp-1", "Imported 1", ProductStatus.IMPORTED)
        _seed_product(db_session, "opt-1", "Optimized 1", ProductStatus.OPTIMIZED)
        _seed_product(db_session, "opt-2", "Optimized 2", ProductStatus.OPTIMIZED)

        # WHY: Filter imported only — should return 1
        resp = auth_client.get("/api/products?status=imported", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        # WHY: Filter optimized — should return 2
        resp = auth_client.get("/api/products?status=optimized", headers=_headers())
        assert resp.json()["total"] == 2

    def test_pagination_page_size(self, auth_client, test_settings, db_session):
        for i in range(7):
            _seed_product(db_session, f"pg-{i}", f"Paginated {i}")

        resp = auth_client.get("/api/products?page=1&page_size=3", headers=_headers())
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 7
        assert data["total_pages"] == 3


# ── Journey 5: Product detail view + update ───────────────────────────────────

class TestJ05ProductDetailAndUpdate:
    """User views product detail and updates title."""

    def test_view_then_update_product(self, auth_client, test_settings, db_session):
        p = _seed_product(db_session, "detail-1", "Stary tytul")

        # View detail
        resp = auth_client.get(f"/api/products/{p.id}", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["title_original"] == "Stary tytul"

        # Update title
        resp = auth_client.put(
            f"/api/products/{p.id}",
            json={"title_original": "Nowy tytul"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["title_original"] == "Nowy tytul"


# ── Journey 6: Optimizer — generate listing (mocked LLM) ─────────────────────

class TestJ06OptimizerGenerate:
    """User generates an optimized listing via the optimizer endpoint."""

    @patch("api.optimizer_routes.optimize_listing", new_callable=AsyncMock)
    def test_generate_listing(self, mock_gen, auth_client, test_settings):
        # WHY: Mock must match OptimizerResponse model exactly
        mock_gen.return_value = {
            "status": "success",
            "marketplace": "amazon_de",
            "brand": "TechBrand",
            "mode": "full",
            "language": "de",
            "listing": {
                "title": "Optymalizowany Tytul",
                "bullet_points": ["B1", "B2"],
                "description": "Opis",
                "backend_keywords": "kw1 kw2",
            },
            "scores": {
                "coverage_pct": 85,
                "coverage_mode": "aggressive",
                "exact_matches_in_title": 1,
                "title_coverage_pct": 90,
                "backend_utilization_pct": 60,
                "backend_byte_size": 200,
                "compliance_status": "PASS",
            },
            "compliance": {"status": "PASS", "issues": []},
            "keyword_intel": {
                "total_analyzed": 1, "tier1_title": 1,
                "tier2_bullets": 0, "tier3_backend": 0,
                "missing_keywords": [], "root_words": [],
            },
            "ranking_juice": {"score": 80, "grade": "B+", "verdict": "Good"},
            "llm_provider": "groq",
            "optimization_source": "direct",
        }
        resp = auth_client.post(
            "/api/optimizer/generate",
            json={
                "product_title": "Kabel USB-C",
                "brand": "TechBrand",
                "keywords": [{"phrase": "usb-c", "search_volume": 1000}],
                "marketplace": "amazon_de",
                "mode": "full",
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"


# ── Journey 7: Optimizer history CRUD ─────────────────────────────────────────

class TestJ07OptimizerHistory:
    """User views optimization history and deletes an old run."""

    def test_history_list_and_delete(self, auth_client, test_settings, db_session):
        run = _seed_optimization(db_session, "History Product")

        # List history
        resp = auth_client.get("/api/optimizer/history", headers=_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1

        # Delete run
        resp = auth_client.delete(f"/api/optimizer/history/{run.id}", headers=_headers())
        assert resp.status_code == 200

        # Verify deleted
        resp = auth_client.get(f"/api/optimizer/history/{run.id}", headers=_headers())
        assert resp.status_code == 404


# ── Journey 8: Optimizer batch generate ───────────────────────────────────────

class TestJ08OptimizerBatch:
    """User generates listings for multiple products at once."""

    @patch("api.optimizer_routes.optimize_listing", new_callable=AsyncMock)
    def test_batch_generate(self, mock_gen, auth_client, test_settings):
        # WHY: Mock must match OptimizerResponse format
        mock_gen.return_value = {
            "status": "success",
            "marketplace": "amazon_de", "brand": "BrandX", "mode": "full", "language": "de",
            "listing": {"title": "T", "bullet_points": ["B"], "description": "D", "backend_keywords": "k"},
            "scores": {"coverage_pct": 80, "coverage_mode": "aggressive", "exact_matches_in_title": 0,
                       "title_coverage_pct": 0, "backend_utilization_pct": 0, "backend_byte_size": 0,
                       "compliance_status": "PASS"},
            "compliance": {"status": "PASS", "issues": []},
            "keyword_intel": {"total_analyzed": 1, "tier1_title": 1, "tier2_bullets": 0,
                              "tier3_backend": 0, "missing_keywords": [], "root_words": []},
            "ranking_juice": {"score": 70, "grade": "B", "verdict": "OK"},
            "llm_provider": "groq", "optimization_source": "direct",
        }
        products = [
            {
                "product_title": f"Batch Product {i}",
                "brand": "BrandX",
                "keywords": [{"phrase": "keyword", "search_volume": 500}],
                "marketplace": "amazon_de",
                "mode": "full",
            }
            for i in range(3)
        ]
        resp = auth_client.post(
            "/api/optimizer/generate-batch",
            json={"products": products},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["succeeded"] == 3


# ── Journey 9: Settings read/update ──────────────────────────────────────────

class TestJ09SettingsReadUpdate:
    """User reads settings, updates store name, reads again to verify."""

    def test_settings_get_returns_defaults(self, auth_client, test_settings, db_session):
        """GET /settings returns default settings even without a user_settings row."""
        # WHY: user_settings is a raw SQL table (not a SQLAlchemy model)
        _create_user_settings_table(db_session)

        resp = auth_client.get("/api/settings", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "general" in data
        assert "notifications" in data
        assert "llm" in data
        # WHY: Default store_name is empty string
        assert isinstance(data["general"]["store_name"], str)

    def test_settings_rejects_api_key_only(self, client, test_settings):
        """Settings must require JWT — API key alone should fail."""
        resp = client.get("/api/settings", headers=_headers())
        assert resp.status_code == 401


# ── Journey 10: Alert config lifecycle ────────────────────────────────────────

class TestJ10AlertConfigLifecycle:
    """User creates an alert config, toggles it, then deletes it."""

    def test_create_toggle_delete_alert(self, auth_client, test_settings, db_session):
        # WHY: create endpoint returns 201
        resp = auth_client.post(
            "/api/monitoring/alerts/config",
            json={
                "alert_type": "price_change",
                "name": "Zmiana ceny > 10%",
                "enabled": True,
                "threshold": 10.0,
                "marketplace": "amazon",
                "cooldown_minutes": 30,
            },
            headers=_headers(),
        )
        assert resp.status_code == 201
        config_id = resp.json()["id"]

        # Toggle off
        resp = auth_client.patch(
            f"/api/monitoring/alerts/config/{config_id}/toggle",
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

        # Delete
        resp = auth_client.delete(
            f"/api/monitoring/alerts/config/{config_id}",
            headers=_headers(),
        )
        assert resp.status_code == 200


# ── Journey 11: Monitoring — track product ────────────────────────────────────

class TestJ11MonitoringTrackProduct:
    """User starts tracking a product and views tracked list."""

    def test_track_and_list(self, auth_client, test_settings, db_session):
        # WHY: track endpoint returns 201
        resp = auth_client.post(
            "/api/monitoring/track",
            json={
                "marketplace": "amazon",
                "product_id": "B0TEST123",
                "product_url": "https://amazon.de/dp/B0TEST123",
                "product_title": "Testowany Produkt",
                "poll_interval_hours": 12,
            },
            headers=_headers(),
        )
        assert resp.status_code == 201
        tracked_id = resp.json()["id"]

        # List tracked products
        resp = auth_client.get("/api/monitoring/tracked", headers=_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["product_id"] == "B0TEST123"

        # Toggle off
        resp = auth_client.patch(
            f"/api/monitoring/track/{tracked_id}/toggle",
            headers=_headers(),
        )
        assert resp.status_code == 200

        # Delete
        resp = auth_client.delete(
            f"/api/monitoring/track/{tracked_id}",
            headers=_headers(),
        )
        assert resp.status_code == 200


# ── Journey 12: EPR status check requires auth ───────────────────────────────

class TestJ12EprStatusAuth:
    """EPR status endpoint requires JWT — blocks API-key-only requests."""

    def test_epr_status_no_jwt_returns_401(self, client, test_settings):
        resp = client.get("/api/epr/status", headers=_headers())
        assert resp.status_code == 401

    def test_epr_status_with_jwt_returns_200(self, auth_client, test_settings):
        resp = auth_client.get("/api/epr/status", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "credentials_configured" in data


# ── Journey 13: Product delete with confirmation ─────────────────────────────

class TestJ13ProductDelete:
    """User deletes a product and it disappears from the list."""

    def test_delete_product_removes_from_list(self, auth_client, test_settings, db_session):
        p = _seed_product(db_session, "del-me", "Do usuniecia")

        # Verify exists
        resp = auth_client.get("/api/products", headers=_headers())
        assert resp.json()["total"] == 1

        # Delete
        resp = auth_client.delete(f"/api/products/{p.id}", headers=_headers())
        assert resp.status_code == 200

        # Verify gone
        resp = auth_client.get("/api/products", headers=_headers())
        assert resp.json()["total"] == 0


# ── Journey 14: Multi-tenant isolation — User B can't see User A's products ──

class TestJ14MultiTenantIsolation:
    """Products from another user must NOT appear in the list."""

    def test_other_user_products_invisible(self, auth_client, test_settings, db_session):
        # WHY: Insert product for a DIFFERENT user
        foreign = Product(
            user_id="other-user-9999-0000-xxxx-yyyyyyyy",
            source_platform="allegro",
            source_id="foreign-1",
            title_original="Produkt innego uzytkownika",
            status=ProductStatus.IMPORTED,
            currency="PLN",
            images=[],
            attributes={},
            marketplace_data={},
        )
        db_session.add(foreign)
        db_session.commit()

        # auth_client = TEST_USER_ID → should see 0 products
        resp = auth_client.get("/api/products", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_other_user_product_detail_404(self, auth_client, test_settings, db_session):
        foreign = Product(
            user_id="other-user-9999-0000-xxxx-yyyyyyyy",
            source_platform="allegro",
            source_id="foreign-detail",
            title_original="Niedostepny",
            status=ProductStatus.IMPORTED,
            currency="PLN",
            images=[],
            attributes={},
            marketplace_data={},
        )
        db_session.add(foreign)
        db_session.commit()
        db_session.refresh(foreign)

        # WHY: Trying to access someone else's product → 404, not 200
        resp = auth_client.get(f"/api/products/{foreign.id}", headers=_headers())
        assert resp.status_code == 404


# ── Journey 15: Import job status requires auth ──────────────────────────────

class TestJ15ImportJobAuth:
    """Import job endpoint rejects unauthenticated requests."""

    def test_job_status_no_jwt_returns_401(self, client, test_settings):
        resp = client.get("/api/import/job/99999", headers=_headers())
        assert resp.status_code == 401

    def test_job_status_with_jwt_nonexistent(self, auth_client, test_settings):
        resp = auth_client.get("/api/import/job/99999", headers=_headers())
        assert resp.status_code == 404


# ── Journey 16: Webhook import with valid secret ─────────────────────────────

class TestJ16WebhookImport:
    """External system sends products via webhook with correct secret."""

    def test_webhook_full_flow(self, client, test_settings):
        # Invalid secret → 401
        resp = client.post(
            "/api/import/webhook",
            json={
                "source": "allegro",
                "data": {"products": [{"source_id": "wh-1", "title": "WH", "source_platform": "allegro"}]},
            },
            headers={"X-Webhook-Secret": "wrong"},
        )
        assert resp.status_code == 401

        # Valid secret → 200
        resp = client.post(
            "/api/import/webhook",
            json={
                "source": "allegro",
                "data": {"products": [{"source_id": "wh-ok", "title": "Webhook OK", "source_platform": "allegro"}]},
            },
            headers={"X-Webhook-Secret": test_settings.webhook_secret},
        )
        assert resp.status_code == 200
        assert resp.json()["success_count"] == 1


# ── Journey 17: Converter store-urls requires auth ───────────────────────────

class TestJ17ConverterAuth:
    """Converter endpoints reject API-key-only and allow JWT-authenticated requests."""

    def test_store_urls_no_jwt_returns_401(self, client, test_settings):
        resp = client.post(
            "/api/converter/store-urls",
            json={"store": "https://allegro.pl/uzytkownik/TestShop"},
            headers=_headers(),
        )
        assert resp.status_code == 401

    def test_marketplaces_is_public(self, client, test_settings):
        resp = client.get("/api/converter/marketplaces", headers=_headers())
        assert resp.status_code == 200


# ── Journey 18: Dashboard stats reflect actual data ──────────────────────────

class TestJ18DashboardReflectsData:
    """Dashboard stats accurately count products by status."""

    def test_stats_count_by_status(self, auth_client, test_settings, db_session):
        _seed_product(db_session, "s-imp-1", "Imported A", ProductStatus.IMPORTED)
        _seed_product(db_session, "s-imp-2", "Imported B", ProductStatus.IMPORTED)
        _seed_product(db_session, "s-opt-1", "Optimized A", ProductStatus.OPTIMIZED)
        _seed_product(db_session, "s-fail-1", "Failed A", ProductStatus.FAILED)

        resp = auth_client.get("/api/products/stats/summary", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 4
        assert data["pending_optimization"] == 2  # imported
        assert data["optimized_products"] == 1
        assert data["failed_products"] == 1


# ── Journey 19: Optimization feedback rating ─────────────────────────────────

class TestJ19OptimizationFeedback:
    """User rates an optimization run (1-5 stars) via listing_history table."""

    def test_rate_optimization(self, auth_client, test_settings, db_session):
        # WHY: Feedback endpoint uses raw SQL on listing_history table, not optimization_runs
        _create_listing_history_table(db_session)

        import uuid
        listing_id = str(uuid.uuid4())
        db_session.execute(
            text("INSERT INTO listing_history (id, brand, marketplace, product_title, title) "
                 "VALUES (:id, :brand, :mp, :pt, :title)"),
            {"id": listing_id, "brand": "TestBrand", "mp": "amazon_de",
             "pt": "Rated Product", "title": "AI Title"},
        )
        db_session.commit()

        resp = auth_client.patch(
            f"/api/optimizer/history/{listing_id}/feedback",
            json={"rating": 4},
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["rating"] == 4


# ── Journey 20: Monitoring dashboard overview ────────────────────────────────

class TestJ20MonitoringDashboard:
    """User views monitoring dashboard with tracked products and alert stats."""

    def test_monitoring_dashboard(self, auth_client, test_settings, db_session):
        # WHY: Dashboard aggregates tracked products + alerts for the user
        resp = auth_client.get("/api/monitoring/dashboard", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["tracked_products"] == 0
        assert data["active_alerts"] == 0

    def test_alert_configs_empty(self, auth_client, test_settings, db_session):
        # WHY: Replaces scheduler_status test (depends on APScheduler init)
        # Verify empty alert configs list for new user
        resp = auth_client.get("/api/monitoring/alerts/configs", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
