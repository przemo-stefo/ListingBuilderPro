# backend/tests/test_import_service.py
# Purpose: ImportService DB operations — create job, import product, batch
# NOT for: HTTP route tests

import pytest
from schemas.product import ProductImport
from models.product import Product, ProductStatus
from models.jobs import ImportJob, JobStatus


class TestImportServiceCreateJob:

    def test_create_job(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        job = svc.create_import_job("allegro", 5, user_id="user-abc")
        assert job.id is not None
        assert job.source == "allegro"
        assert job.total_products == 5
        assert job.status == JobStatus.RUNNING
        assert job.user_id == "user-abc"

    def test_get_job_status(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        job = svc.create_import_job("amazon", 3, user_id="user-abc")
        fetched = svc.get_job_status(job.id, user_id="user-abc")
        assert fetched.id == job.id

    def test_get_job_wrong_user_returns_none(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        job = svc.create_import_job("amazon", 3, user_id="user-abc")
        assert svc.get_job_status(job.id, user_id="user-other") is None

    def test_get_nonexistent_job(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        assert svc.get_job_status(9999) is None


class TestImportServiceProduct:

    def _make_product_data(self, source_id="test-123"):
        return ProductImport(
            source_platform="allegro",
            source_id=source_id,
            title="Test Product",
            description="A test product",
            price=29.99,
            currency="PLN",
        )

    def test_import_new_product(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        data = self._make_product_data()
        product = svc.import_product(data)
        assert product.id is not None
        assert product.title_original == "Test Product"
        assert product.status == ProductStatus.IMPORTED

    def test_import_duplicate_updates(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        data1 = self._make_product_data("dup-123")
        svc.import_product(data1)

        data2 = ProductImport(
            source_platform="allegro",
            source_id="dup-123",
            title="Updated Title",
            price=39.99,
        )
        product = svc.import_product(data2)
        assert product.title_original == "Updated Title"
        assert product.price == 39.99

    def test_import_batch_success(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        products = [
            self._make_product_data(f"batch-{i}") for i in range(3)
        ]
        result = svc.import_batch(products, source="allegro")
        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert result["job_id"] is not None

    def test_import_batch_empty(self, db_session):
        from services.import_service import ImportService
        svc = ImportService(db_session)
        result = svc.import_batch([], source="allegro")
        assert result["success_count"] == 0
