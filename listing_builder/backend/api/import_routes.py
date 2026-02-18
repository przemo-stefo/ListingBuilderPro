# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/import_routes.py
# Purpose: API routes for product import from scrapers
# NOT for: AI optimization or export logic

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from api.dependencies import get_user_id
from schemas import ProductImport, WebhookPayload, ImportJobResponse
from services.import_service import ImportService
from config import settings
from typing import List, Literal, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
import hmac
import structlog

logger = structlog.get_logger()

# WHY: Rate limiter prevents batch import abuse
limiter = Limiter(key_func=get_remote_address)
# WHY: Server-side limit prevents DoS via huge payloads
MAX_BATCH_SIZE = 500

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
        # WHY: Same guard as /batch — prevents DoS via oversized webhook payloads
        if len(products_data) > MAX_BATCH_SIZE:
            raise HTTPException(status_code=400, detail=f"Max {MAX_BATCH_SIZE} products per webhook call")

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


VALID_SOURCES = {"allegro", "amazon", "ebay", "kaufland", "manual"}


class ScrapeRequest(BaseModel):
    """WHY: Typed request for URL scraping — validates URL format before processing."""
    url: str
    marketplace: Optional[str] = None


@router.post("/scrape-url")
@limiter.limit("10/minute")
async def scrape_product_url(
    request: Request,
    body: ScrapeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Scrape product data from a marketplace URL.
    Returns scraped data WITHOUT importing — user reviews first.
    """
    from utils.url_validator import validate_marketplace_url

    # WHY: Detect marketplace from URL domain if not specified
    marketplace = body.marketplace
    if not marketplace:
        from urllib.parse import urlparse
        hostname = urlparse(body.url).hostname or ""
        if "allegro" in hostname:
            marketplace = "allegro"
        elif "amazon" in hostname:
            marketplace = "amazon"
        elif "ebay" in hostname:
            marketplace = "ebay"
        elif "kaufland" in hostname:
            marketplace = "kaufland"

    # SECURITY: Validate URL domain
    try:
        validate_marketplace_url(body.url, marketplace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if marketplace != "allegro":
        raise HTTPException(status_code=400, detail=f"Scraping not yet supported for {marketplace}")

    # WHY: 2-tier fallback: seller API → Scrape.do
    # Public API (Client Credentials) doesn't work — Allegro requires app verification
    # for GET /offers/listing, and GET /offers/{id} endpoint doesn't exist (406).
    from services.scraper.allegro_scraper import extract_offer_id
    from services.allegro_api import get_access_token, fetch_offer_details

    offer_id = extract_offer_id(body.url)
    allegro_token = await get_access_token(db, user_id)

    if allegro_token and offer_id:
        data = await fetch_offer_details(offer_id, allegro_token)
        if not data.get("error"):
            if data.get("price"):
                try:
                    data["price"] = float(str(data["price"]).replace(",", ".").replace(" ", ""))
                except (ValueError, AttributeError):
                    data["price"] = None
            return {"status": "success", "product": data, "source": "allegro_api"}

    # Fallback: Scrape.do (paid, has monthly limits)
    from services.scraper.allegro_scraper import scrape_allegro_product
    from dataclasses import asdict
    product = await scrape_allegro_product(body.url)

    if product.error:
        # WHY: Clear message when both methods fail
        error_msg = product.error
        if "limit" in error_msg.lower() or "exceeded" in error_msg.lower():
            error_msg = "Połącz konto Allegro w Konwerterze — scraping niedostępny"
        raise HTTPException(status_code=502, detail=f"Scraping failed: {error_msg}")

    data = asdict(product)
    if data.get("price"):
        try:
            data["price"] = float(data["price"].replace(",", ".").replace(" ", ""))
        except (ValueError, AttributeError):
            data["price"] = None

    return {"status": "success", "product": data, "source": "scrape_do"}


@router.post("/product")
@limiter.limit("30/minute")
async def import_single_product(
    request: Request,
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
@limiter.limit("5/minute")
async def import_batch(
    request: Request,
    products: List[ProductImport],
    source: Literal["allegro", "amazon", "ebay", "kaufland", "manual"] = "allegro",
    db: Session = Depends(get_db)
):
    """
    Import multiple products as a batch.
    Alternative to webhook endpoint.
    """
    # WHY: Server-side guard against oversized payloads (frontend also caps at 500)
    if len(products) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Max {MAX_BATCH_SIZE} products per batch")
    if len(products) == 0:
        raise HTTPException(status_code=400, detail="No products provided")

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
