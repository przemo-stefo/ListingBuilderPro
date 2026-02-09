# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/import_routes.py
# Purpose: API routes for product import from scrapers
# NOT for: AI optimization or export logic

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProductImport, WebhookPayload, ImportJobResponse
from services.import_service import ImportService
from config import settings
from typing import List, Optional
import hmac
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/import", tags=["Import"])


def verify_webhook_secret(x_webhook_secret: Optional[str] = Header(None)):
    """
    Verify webhook secret from n8n.
    This prevents unauthorized webhook calls.
    """
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, settings.webhook_secret):
        logger.warning("invalid_webhook_secret", provided_length=len(x_webhook_secret) if x_webhook_secret else 0)
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return True


@router.post("/webhook", dependencies=[Depends(verify_webhook_secret)])
async def receive_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Main webhook endpoint for n8n scraper.
    Receives product data and imports into database.

    Headers required:
        X-Webhook-Secret: Your webhook secret token

    Body:
        {
            "source": "allegro",
            "event_type": "product.import",
            "data": {
                "products": [...]  // Array of products
            }
        }
    """
    logger.info("webhook_received", source=payload.source, event=payload.event_type)

    try:
        service = ImportService(db)

        # Extract products from payload
        products_data = payload.data.get("products", [])
        if not products_data:
            raise HTTPException(status_code=400, detail="No products in payload")

        # Validate and parse products
        products = [ProductImport(**p) for p in products_data]

        # Import batch
        result = service.import_batch(products, source=payload.source)

        return {
            "status": "success",
            "message": f"Imported {result['success_count']} products",
            **result
        }

    except Exception as e:
        logger.error("webhook_processing_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Import failed")


@router.post("/product")
async def import_single_product(
    product: ProductImport,
    db: Session = Depends(get_db)
):
    """
    Import a single product manually.
    Useful for testing or manual imports.
    """
    logger.info("manual_product_import", source_id=product.source_id)

    try:
        service = ImportService(db)
        result = service.import_product(product)
        return {"status": "success", "product_id": result.id}
    except Exception as e:
        logger.error("product_import_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Product import failed")


@router.post("/batch")
async def import_batch(
    products: List[ProductImport],
    source: str = "allegro",
    db: Session = Depends(get_db)
):
    """
    Import multiple products as a batch.
    Alternative to webhook endpoint.
    """
    logger.info("batch_import_started", count=len(products), source=source)

    try:
        service = ImportService(db)
        result = service.import_batch(products, source)
        return {"status": "success", **result}
    except Exception as e:
        logger.error("batch_import_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch import failed")


@router.get("/job/{job_id}", response_model=ImportJobResponse)
async def get_import_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get import job status by ID.
    """
    service = ImportService(db)
    job = service.get_job_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
