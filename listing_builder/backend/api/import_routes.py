# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/import_routes.py
# Purpose: API routes for product import from scrapers
# NOT for: AI optimization or export logic

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field, ValidationError
from database import get_db
from api.dependencies import require_user_id
from schemas import ProductImport, WebhookPayload, ImportJobResponse
from services.import_service import ImportService
from config import settings
from typing import List, Literal, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import hmac
import structlog

logger = structlog.get_logger()


def _parse_price(raw) -> Optional[float]:
    """WHY: DRY — price string→float conversion used by all 3 import tiers."""
    if raw is None:
        return None
    try:
        return float(str(raw).replace(",", ".").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


# WHY: Rate limiter prevents batch import abuse
limiter = Limiter(key_func=get_remote_address)
# WHY: Server-side limit prevents DoS via huge payloads
MAX_BATCH_SIZE = 500

router = APIRouter(prefix="/api/import", tags=["Import"])


def _handle_import_error(e: Exception, context: str):
    """WHY: DRY — same error handling pattern used by webhook, single, and batch endpoints."""
    if isinstance(e, IntegrityError):
        logger.error(f"{context}_integrity", error=str(e))
        raise HTTPException(status_code=409, detail="Produkt o tym ID już istnieje na tej platformie")
    if isinstance(e, ValidationError):
        logger.error(f"{context}_validation", error=str(e))
        first_err = e.errors()[0] if e.errors() else {}
        field = first_err.get("loc", ["?"])[-1]
        raise HTTPException(status_code=400, detail=f"Niepoprawne dane: {field}")
    if isinstance(e, HTTPException):
        raise
    if isinstance(e, TimeoutError):
        logger.error(f"{context}_timeout")
        raise HTTPException(status_code=504, detail="Timeout — spróbuj ponownie")
    logger.error(f"{context}_failed", error=str(e))
    raise HTTPException(status_code=500, detail="Nieoczekiwany błąd importu")


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
@limiter.limit("10/minute")
async def receive_webhook(
    request: Request,
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
    logger.info("webhook_received", source=payload.source, event_type=payload.event_type)

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

        # WHY: Webhook imports use "webhook" user_id — not tied to a user session
        # Products imported via webhook must be claimed later by the actual user
        result = service.import_batch(products, source=payload.source, user_id="webhook")

        return {
            "status": "success",
            "message": f"Imported {result['success_count']} products",
            **result
        }

    except Exception as e:
        _handle_import_error(e, "webhook")


VALID_SOURCES = {"allegro", "amazon", "ebay", "kaufland", "rozetka", "aliexpress", "temu", "manual"}

# WHY: Max 100 offers per import from connected account — balances speed vs API rate limits
MAX_ALLEGRO_IMPORT = 100


class AllegroAccountImportRequest(BaseModel):
    """WHY: Typed request for importing from connected Allegro account."""
    offer_ids: List[str] = Field(..., min_length=1, max_length=MAX_ALLEGRO_IMPORT)


@router.post("/from-allegro")
@limiter.limit("5/minute")
async def import_from_allegro_account(
    request: Request,
    body: AllegroAccountImportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    Import products from connected Allegro account by offer IDs.
    Fetches full details via Allegro API, then imports into product database.
    """
    from services.allegro_api import get_access_token, fetch_offer_details

    access_token = await get_access_token(db, user_id)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Allegro nie jest połączone. Połącz konto w Integracje."
        )

    products = []
    errors = []

    for offer_id in body.offer_ids:
        try:
            data = await fetch_offer_details(offer_id, access_token)
            if data.get("error"):
                errors.append(f"{offer_id}: {data['error']}")
                continue

            # WHY: Convert Allegro API response to ProductImport schema
            price = _parse_price(data.get("price"))

            product = ProductImport(
                source_platform="allegro",
                source_id=data.get("source_id", offer_id),
                source_url=data.get("source_url", f"https://allegro.pl/oferta/{offer_id}"),
                title=data.get("title", ""),
                description=data.get("description", ""),
                category=data.get("category", ""),
                brand=data.get("brand", ""),
                price=price,
                currency=data.get("currency", "PLN"),
                images=data.get("images", []),
                attributes={
                    "parameters": data.get("parameters", {}),
                    "ean": data.get("ean", ""),
                    "manufacturer": data.get("manufacturer", ""),
                },
            )
            products.append(product)
        except Exception as e:
            errors.append(f"{offer_id}: {str(e)}")

    if not products:
        raise HTTPException(
            status_code=400,
            detail=f"Nie udało się pobrać żadnej oferty. Błędy: {'; '.join(errors)}"
        )

    try:
        service = ImportService(db)
        result = service.import_batch(products, source="allegro-account", user_id=user_id)
        result["errors"] = errors
        return {"status": "success", **result}
    except Exception as e:
        _handle_import_error(e, "allegro_account_import")


class ScrapeRequest(BaseModel):
    """WHY: Typed request for URL scraping — validates URL format before processing."""
    # SECURITY: Max 2048 chars prevents ReDoS on regex-heavy parsers + memory abuse
    url: str = Field(..., max_length=2048)
    marketplace: Optional[str] = None


@router.post("/scrape-url")
@limiter.limit("10/minute")
async def scrape_product_url(
    request: Request,
    body: ScrapeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
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
        elif "rozetka" in hostname:
            marketplace = "rozetka"
        elif "aliexpress" in hostname:
            marketplace = "aliexpress"
        elif "temu" in hostname:
            marketplace = "temu"

    # SECURITY: Validate URL domain
    try:
        validate_marketplace_url(body.url, marketplace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # WHY: Rozetka, AliExpress, Temu use the same scrape→parse→return pattern
    scraper_map = {
        "rozetka": ("services.scraper.rozetka_scraper", "scrape_rozetka_product", "Rozetka"),
        "aliexpress": ("services.scraper.aliexpress_scraper", "scrape_aliexpress_product", "AliExpress"),
        "temu": ("services.scraper.temu_scraper", "scrape_temu_product", "Temu (beta)"),
    }
    if marketplace in scraper_map:
        from dataclasses import asdict
        from importlib import import_module

        module_path, func_name, label = scraper_map[marketplace]
        scraper_fn = getattr(import_module(module_path), func_name)
        product = await scraper_fn(body.url)
        if not product.error:
            data = asdict(product)
            data["price"] = _parse_price(data.get("price"))
            logger.info(f"scrape_url_{marketplace}_success", source_id=product.source_id)
            return {"status": "success", "product": data, "source": f"{marketplace}_scraper"}
        raise HTTPException(
            status_code=503,
            detail=product.error or f"Nie udało się pobrać oferty z {label}"
        )

    if marketplace != "allegro":
        raise HTTPException(status_code=400, detail=f"Import po URL nie jest jeszcze wspierany dla {marketplace}")

    # WHY 3-tier: OAuth API (own offers) → /offers/listing (any offer) → Scrape.do (DataDome bypass)
    # Architecture agreed 2026-02-27 in sessions 1816268a + a638d1c3
    from services.scraper.allegro_scraper import extract_offer_id, scrape_allegro_product
    from services.allegro_api import get_access_token, fetch_offer_details, fetch_offer_via_listing
    from dataclasses import asdict

    # WHY: Normalize business.allegro.pl → allegro.pl
    clean_url = body.url.replace("business.allegro.pl", "allegro.pl")
    offer_id = extract_offer_id(clean_url)

    if not offer_id:
        raise HTTPException(status_code=400, detail="Nie udało się wyciągnąć ID oferty z URL. Sprawdź link.")

    # Tier 1: User OAuth → /sale/product-offers — full data (own offers only)
    allegro_token = await get_access_token(db, user_id)
    if allegro_token:
        data = await fetch_offer_details(offer_id, allegro_token)
        if not data.get("error"):
            data["price"] = _parse_price(data.get("price"))
            logger.info("scrape_url_tier1_success", offer_id=offer_id)
            return {"status": "success", "product": data, "source": "allegro_api"}
        logger.info("scrape_url_tier1_failed", offer_id=offer_id, error=data.get("error"))

    # Tier 2: User OAuth → /offers/listing — basic data for ANY public offer
    if allegro_token:
        data = await fetch_offer_via_listing(offer_id, allegro_token)
        if not data.get("error"):
            data["price"] = _parse_price(data.get("price"))
            logger.info("scrape_url_tier2_success", offer_id=offer_id, images=len(data.get("images", [])))
            return {"status": "success", "product": data, "source": "allegro_listing_api"}
        logger.info("scrape_url_tier2_failed", offer_id=offer_id, error=data.get("error"))

    # Tier 3: Scrape.do — DataDome bypass, works for ANY offer without OAuth
    # WHY: Agreed architecture (2026-02-27). Handles anti-bot protection.
    # Free plan: 1000 req/month, resets 1st of each month.
    product = await scrape_allegro_product(clean_url)
    if not product.error:
        data = asdict(product)
        data["price"] = _parse_price(data.get("price"))
        logger.info("scrape_url_tier3_success", offer_id=offer_id, images=len(data.get("images", [])))
        return {"status": "success", "product": data, "source": "scrape_do"}

    # All 3 tiers failed — clear error with guidance
    scrape_error = product.error or ""
    logger.error("scrape_url_all_tiers_failed", offer_id=offer_id, scrape_error=scrape_error[:100])

    if "limit" in scrape_error.lower() or "exceeded" in scrape_error.lower():
        error_msg = (
            "Limit scrapowania wyczerpany (resetuje się 1. dnia miesiąca). "
            "Połącz konto Allegro (Integracje → Allegro OAuth) aby importować swoje oferty bez limitu."
        )
    elif not allegro_token:
        error_msg = (
            "Połącz konto Allegro (Integracje → Allegro OAuth), aby importować produkty. "
            "Bez połączonego konta dostępny jest tylko scraping (limit wyczerpany)."
        )
    else:
        error_msg = (
            f"Nie udało się pobrać oferty {offer_id}. "
            "Sprawdź czy link jest poprawny i oferta aktywna."
        )

    raise HTTPException(status_code=503, detail=error_msg)


@router.post("/product")
@limiter.limit("30/minute")
async def import_single_product(
    request: Request,
    product: ProductImport,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    Import a single product manually.
    Useful for testing or manual imports.
    """
    logger.info("manual_product_import", source_id=product.source_id)

    try:
        service = ImportService(db)
        result = service.import_product(product, user_id=user_id)
        return {"status": "success", "product_id": result.id}
    except Exception as e:
        _handle_import_error(e, "product_import")


@router.post("/batch")
@limiter.limit("5/minute")
async def import_batch(
    request: Request,
    products: List[ProductImport],
    source: Literal["allegro", "amazon", "ebay", "kaufland", "rozetka", "aliexpress", "temu", "manual"] = "allegro",
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
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
        result = service.import_batch(products, source, user_id=user_id)
        return {"status": "success", **result}
    except Exception as e:
        _handle_import_error(e, "batch_import")


@router.get("/job/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    Get import job status by ID.
    WHY require_user_id: Prevents cross-tenant job data exposure.
    """
    service = ImportService(db)
    # WHY: user_id filter prevents IDOR — user can only see their own jobs
    job = service.get_job_status(job_id, user_id=user_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
