# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/import_service.py
# Purpose: Handle product imports from scrapers (n8n webhook)
# NOT for: AI optimization or marketplace publishing

from sqlalchemy.orm import Session
from models import Product, ImportJob, ProductStatus, JobStatus
from schemas import ProductImport
from typing import List, Dict, Any
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()


class ImportService:
    """
    Service for importing products from external scrapers.
    Handles webhook data validation, deduplication, and storage.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_import_job(self, source: str, total_products: int) -> ImportJob:
        """
        Create a new import job to track batch import.
        """
        job = ImportJob(
            source=source,
            total_products=total_products,
            status=JobStatus.RUNNING,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info("import_job_created", job_id=job.id, source=source, total=total_products)
        return job

    def import_product(self, data: ProductImport, job_id: int = None) -> Product:
        """
        Import a single product.
        Checks for duplicates by source_id and updates if exists.

        Args:
            data: Validated product data from webhook
            job_id: Optional import job ID for tracking

        Returns:
            Product: Created or updated product
        """
        # Check if product already exists
        existing = self.db.query(Product).filter(
            Product.source_id == data.source_id,
            Product.source_platform == data.source_platform
        ).first()

        if existing:
            logger.info("product_exists_updating", source_id=data.source_id)
            # Update existing product
            existing.title_original = data.title
            existing.description_original = data.description
            existing.price = data.price
            existing.currency = data.currency
            existing.images = data.images
            existing.attributes = data.attributes
            existing.category = data.category
            existing.brand = data.brand
            existing.source_url = data.source_url
            existing.status = ProductStatus.IMPORTED  # Reset to imported
            product = existing
        else:
            # Create new product
            product = Product(
                source_platform=data.source_platform,
                source_id=data.source_id,
                source_url=data.source_url,
                title_original=data.title,
                description_original=data.description,
                category=data.category,
                brand=data.brand,
                price=data.price,
                currency=data.currency,
                images=data.images,
                attributes=data.attributes,
                status=ProductStatus.IMPORTED,
            )
            self.db.add(product)
            logger.info("product_created", source_id=data.source_id)

        self.db.commit()
        self.db.refresh(product)
        return product

    def import_batch(self, products: List[ProductImport], source: str = "allegro") -> Dict[str, Any]:
        """
        Import multiple products in batch.
        Creates import job and processes each product.

        Returns:
            Dict with job_id, success_count, failed_count, errors
        """
        job = self.create_import_job(source, len(products))
        success_count = 0
        failed_count = 0
        errors = []

        for product_data in products:
            try:
                self.import_product(product_data, job.id)
                success_count += 1
                job.processed_products = success_count
                self.db.commit()
            except Exception as e:
                # WHY: rollback dirty session before updating job counters
                self.db.rollback()
                failed_count += 1
                job.failed_products = failed_count
                error_msg = f"Failed to import {product_data.source_id}: {str(e)}"
                errors.append(error_msg)
                logger.error("product_import_failed", error=str(e), source_id=product_data.source_id)
                self.db.commit()

        # WHY: Partial success (some OK, some failed) should not mark entire job as FAILED
        if failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif success_count == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED  # partial success, errors logged in error_log
        job.completed_at = datetime.now(timezone.utc)
        job.error_log = errors
        self.db.commit()

        logger.info("batch_import_completed", job_id=job.id, success=success_count, failed=failed_count)

        return {
            "job_id": job.id,
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    def get_job_status(self, job_id: int) -> ImportJob:
        """Get import job by ID"""
        return self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
