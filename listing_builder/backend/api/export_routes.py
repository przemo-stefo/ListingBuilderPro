# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/export_routes.py
# Purpose: API routes for publishing to marketplaces
# NOT for: Import or AI optimization

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from schemas import BulkJobCreate, BulkJobResponse
from services.export_service import ExportService
from api.dependencies import require_premium
import structlog

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/export", tags=["Export"])


ALLOWED_MARKETPLACES = {"amazon", "ebay", "kaufland"}


@router.post("/publish/{product_id}")
@limiter.limit("5/minute")
async def publish_product(
    request: Request,
    product_id: int,
    marketplace: str,
    db: Session = Depends(get_db),
):
    """
    Publish a single product to marketplace.

    Args:
        product_id: Product ID to publish
        marketplace: amazon, ebay, or kaufland

    Returns:
        Publishing result
    """
    require_premium(request, db)

    # WHY: Validate marketplace before passing to service — prevents unexpected behavior
    if marketplace not in ALLOWED_MARKETPLACES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported marketplace. Allowed: {', '.join(sorted(ALLOWED_MARKETPLACES))}",
        )

    logger.info("publish_requested", product_id=product_id, marketplace=marketplace)

    try:
        service = ExportService(db)
        result = service.publish_product(product_id, marketplace)

        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("publish_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail="Publishing failed")


@router.post("/bulk-publish", response_model=BulkJobResponse)
@limiter.limit("2/minute")
async def bulk_publish(
    request: Request,
    job_data: BulkJobCreate,
    db: Session = Depends(get_db),
):
    """
    Publish multiple products to marketplace.
    Creates a bulk job and processes all products.

    Body:
        {
            "job_type": "publish",
            "target_marketplace": "amazon",
            "product_ids": [1, 2, 3, 4, 5]
        }
    """
    require_premium(request, db)

    logger.info("bulk_publish_requested",
                count=len(job_data.product_ids),
                marketplace=job_data.target_marketplace)

    try:
        service = ExportService(db)
        job = service.bulk_publish(job_data.product_ids, job_data.target_marketplace)
        return job
    except Exception as e:
        logger.error("bulk_publish_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Bulk publishing failed")


@router.get("/marketplaces")
@limiter.limit("30/minute")
async def list_marketplaces(request: Request):
    """
    List available marketplaces.
    """
    return {
        "marketplaces": [
            {
                "id": "amazon",
                "name": "Amazon",
                "regions": ["eu-west-1", "us-east-1"],
                "status": "available"
            },
            {
                "id": "ebay",
                "name": "eBay",
                "regions": ["EBAY_DE", "EBAY_US"],
                "status": "available"
            },
            {
                "id": "kaufland",
                "name": "Kaufland",
                "regions": ["DE", "PL", "CZ"],
                "status": "available"
            }
        ]
    }
