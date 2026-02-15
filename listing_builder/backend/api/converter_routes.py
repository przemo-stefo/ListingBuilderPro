# backend/api/converter_routes.py
# Purpose: API endpoints for Allegro→Marketplace conversion pipeline
# NOT for: Business logic (that's in services/converter/)

import asyncio
import re
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

import structlog

from config import settings
from database import get_db
from services.allegro_api import fetch_seller_offers, get_access_token

limiter = Limiter(key_func=get_remote_address)
from services.scraper.allegro_scraper import (
    scrape_allegro_product,
    scrape_allegro_batch,
    scrape_allegro_store_urls,
    AllegroProduct,
)
from services.converter.ai_translator import AITranslator
from services.converter.converter_service import (
    convert_product,
    convert_batch,
    create_store_job,
    get_store_job,
    process_store_job,
    ConvertedProduct,
)
from services.converter.template_generator import (
    generate_template,
    get_filename,
    get_content_type,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/converter", tags=["converter"])


# ── Request/Response models ───────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    """Request to scrape Allegro product URLs."""
    urls: List[str]
    delay: float = 3.0  # Seconds between requests

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        if not v:
            raise ValueError("At least one URL required")
        if len(v) > 50:
            raise ValueError("Max 50 URLs per request")
        for url in v:
            # WHY: Strict hostname check prevents SSRF — "allegro.pl" substring
            # would match evil.com/allegro.pl or allegro.pl.evil.com
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if not (host == "allegro.pl" or host.endswith(".allegro.pl")):
                raise ValueError(f"Not an Allegro URL: {url}")
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid URL scheme: {url}")
        return v


class GPSRData(BaseModel):
    """GPSR and manufacturer data (user provides once, reused for all products)."""
    manufacturer_contact: str = ""
    manufacturer_address: str = ""
    manufacturer_city: str = ""
    manufacturer_country: str = ""
    country_of_origin: str = ""
    safety_attestation: str = ""
    responsible_person_type: str = ""
    responsible_person_name: str = ""
    responsible_person_address: str = ""
    responsible_person_country: str = ""
    # Marketplace-specific category IDs
    amazon_browse_node: str = ""
    amazon_product_type: str = ""
    ebay_category_id: str = ""
    kaufland_category: str = ""


class ConvertRequest(BaseModel):
    """Request to convert scraped products to marketplace template."""
    urls: List[str]
    marketplace: str  # "amazon", "ebay", or "kaufland"
    gpsr_data: GPSRData = GPSRData()
    eur_rate: float = 0.23
    delay: float = 3.0

    @field_validator("marketplace")
    @classmethod
    def validate_marketplace(cls, v):
        allowed = ["amazon", "ebay", "kaufland"]
        if v not in allowed:
            raise ValueError(f"marketplace must be one of: {allowed}")
        return v

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        if not v:
            raise ValueError("At least one URL required")
        if len(v) > 50:
            raise ValueError("Max 50 URLs per request")
        for url in v:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if not (host == "allegro.pl" or host.endswith(".allegro.pl")):
                raise ValueError(f"Not an Allegro URL: {url}")
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid URL scheme: {url}")
        return v


class StoreUrlsRequest(BaseModel):
    """Request to fetch product URLs from an Allegro store."""
    store: str

    @field_validator("store")
    @classmethod
    def validate_store(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Store name or URL required")
        # Allow raw name or full allegro.pl URL
        if "allegro.pl" not in v and not re.match(r'^[\w-]+$', v):
            raise ValueError("Invalid store name — use letters, numbers, hyphens")
        return v


class StoreUrlsResponse(BaseModel):
    store_name: str
    urls: List[str]
    total: int
    error: Optional[str] = None
    capped: bool = False


class StoreConvertRequest(BaseModel):
    """Request to start async store conversion job."""
    urls: List[str]
    marketplace: str
    gpsr_data: GPSRData = GPSRData()
    eur_rate: float = 0.23

    @field_validator("marketplace")
    @classmethod
    def validate_marketplace(cls, v):
        allowed = ["amazon", "ebay", "kaufland"]
        if v not in allowed:
            raise ValueError(f"marketplace must be one of: {allowed}")
        return v

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        if not v:
            raise ValueError("At least one URL required")
        if len(v) > 300:
            raise ValueError("Max 300 URLs per store conversion")
        return v


class StoreJobStatus(BaseModel):
    job_id: str
    status: str
    total: int
    scraped: int
    converted: int
    failed: int
    download_ready: bool


class ScrapeResponse(BaseModel):
    """Response from scraping endpoint."""
    total: int
    succeeded: int
    failed: int
    products: List[dict]


class ConvertResponse(BaseModel):
    """Response from convert endpoint (JSON mode)."""
    total: int
    succeeded: int
    failed: int
    marketplace: str
    products: List[dict]
    warnings: List[str]


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/scrape", response_model=ScrapeResponse)
@limiter.limit("5/minute")
async def scrape_allegro(request: Request, body: ScrapeRequest = None):
    """Scrape product data from Allegro URLs.

    Returns structured product data (title, EAN, description, images,
    parameters) for each URL. Use this to preview scraped data before
    converting to a marketplace template.
    """
    logger.info("scrape_request", urls_count=len(body.urls))

    products = await scrape_allegro_batch(body.urls, delay=body.delay)

    succeeded = sum(1 for p in products if not p.error)

    return ScrapeResponse(
        total=len(products),
        succeeded=succeeded,
        failed=len(products) - succeeded,
        products=[p.to_dict() for p in products],
    )


@router.post("/convert", response_model=ConvertResponse)
@limiter.limit("5/minute")
async def convert_to_marketplace(request: Request, body: ConvertRequest = None):
    """Full pipeline: Scrape Allegro → Translate → Map → Return JSON.

    Use this endpoint to preview converted data before downloading
    the template file. Returns all mapped fields and warnings.
    """
    logger.info(
        "convert_request",
        urls_count=len(body.urls),
        marketplace=body.marketplace,
    )

    # Step 1: Scrape
    scraped = await scrape_allegro_batch(body.urls, delay=body.delay)

    # Step 2: Initialize AI translator
    translator = AITranslator(groq_api_key=settings.groq_api_key)

    # Step 3: Convert
    converted = convert_batch(
        products=scraped,
        marketplace=body.marketplace,
        translator=translator,
        gpsr_data=body.gpsr_data.model_dump(),
        eur_rate=body.eur_rate,
    )

    succeeded = sum(1 for c in converted if not c.error)
    all_warnings = []
    for c in converted:
        all_warnings.extend(c.warnings)

    return ConvertResponse(
        total=len(converted),
        succeeded=succeeded,
        failed=len(converted) - succeeded,
        marketplace=body.marketplace,
        products=[
            {
                "source_url": c.source_url,
                "source_id": c.source_id,
                "fields": c.fields,
                "warnings": c.warnings,
                "error": c.error,
            }
            for c in converted
        ],
        warnings=all_warnings,
    )


@router.post("/download")
@limiter.limit("3/minute")
async def download_template(request: Request, body: ConvertRequest = None):
    """Full pipeline: Scrape → Translate → Map → Download CSV/TSV file.

    Returns a downloadable file:
    - Amazon: Tab-separated .tsv (flat file format)
    - eBay: Comma-separated .csv
    - Kaufland: Semicolon-separated .csv (UTF-8-BOM)
    """
    logger.info(
        "download_request",
        urls_count=len(body.urls),
        marketplace=body.marketplace,
    )

    # Step 1: Scrape
    scraped = await scrape_allegro_batch(body.urls, delay=body.delay)

    # Step 2: Translate + Convert
    translator = AITranslator(groq_api_key=settings.groq_api_key)
    converted = convert_batch(
        products=scraped,
        marketplace=body.marketplace,
        translator=translator,
        gpsr_data=body.gpsr_data.model_dump(),
        eur_rate=body.eur_rate,
    )

    # Step 3: Generate file
    file_bytes = generate_template(converted, body.marketplace)
    filename = get_filename(body.marketplace)
    content_type = get_content_type(body.marketplace)

    succeeded = sum(1 for c in converted if not c.error)
    logger.info("download_generated", marketplace=body.marketplace, products=succeeded)

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Products-Total": str(len(converted)),
            "X-Products-Succeeded": str(succeeded),
        },
    )


@router.get("/marketplaces")
async def list_marketplaces():
    """List supported target marketplaces and their output formats."""
    return {
        "marketplaces": [
            {
                "id": "amazon",
                "name": "Amazon.de",
                "format": "TSV (Tab-separated)",
                "extension": ".tsv",
                "description": "Amazon Flat File format compatible with Seller Central upload",
            },
            {
                "id": "ebay",
                "name": "eBay.de",
                "format": "CSV (Comma-separated)",
                "extension": ".csv",
                "description": "eBay File Exchange bulk listing format",
            },
            {
                "id": "kaufland",
                "name": "Kaufland.de",
                "format": "CSV (Semicolon-separated, UTF-8-BOM)",
                "extension": ".csv",
                "description": "Kaufland Seller Portal product data template",
            },
        ]
    }


# ── Store endpoints ──────────────────────────────────────────────────────

@router.post("/store-urls", response_model=StoreUrlsResponse)
@limiter.limit("3/minute")
async def get_store_urls(request: Request, body: StoreUrlsRequest):
    """Fetch all product URLs from an Allegro store page.

    Accepts store name (e.g. 'electronics-shop-pl') or full URL.
    Scrapes up to 5 pages (~300 products max).
    """
    logger.info("store_urls_request", store=body.store)
    result = await scrape_allegro_store_urls(body.store)
    return StoreUrlsResponse(**result)


@router.post("/store-convert")
@limiter.limit("2/minute")
async def start_store_convert(
    request: Request,
    body: StoreConvertRequest,
    db: Session = Depends(get_db),
):
    """Start async conversion of store products.

    WHY get_access_token: If Allegro OAuth is connected, use REST API
    instead of Scrape.do — free, faster, no monthly limits.
    """
    # WHY try API first: Allegro API = free + fast, Scrape.do = paid + slow
    allegro_token = await get_access_token(db)

    job_id = create_store_job(body.urls, body.marketplace)
    logger.info("store_convert_started", job_id=job_id,
                urls=len(body.urls), marketplace=body.marketplace,
                method="api" if allegro_token else "scraper")

    asyncio.create_task(
        process_store_job(
            job_id=job_id,
            urls=body.urls,
            marketplace=body.marketplace,
            gpsr_data=body.gpsr_data.model_dump(),
            eur_rate=body.eur_rate,
            groq_api_key=settings.groq_api_key,
            allegro_token=allegro_token,
        )
    )

    return {"job_id": job_id, "total": len(body.urls), "status": "processing"}


@router.get("/store-job/{job_id}", response_model=StoreJobStatus)
async def get_store_job_status(job_id: str):
    """Get the status of a store conversion job."""
    job = get_store_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return StoreJobStatus(
        job_id=job_id,
        status=job["status"],
        total=job["total"],
        scraped=job["scraped"],
        converted=job["converted"],
        failed=job["failed"],
        download_ready=job["status"] == "done" and job["file_bytes"] is not None,
    )


@router.get("/store-job/{job_id}/download")
async def download_store_job(job_id: str):
    """Download the converted file for a completed store job."""
    job = get_store_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job not yet complete")
    if not job["file_bytes"]:
        raise HTTPException(status_code=404, detail="No products converted successfully")

    marketplace = job["marketplace"]
    filename = get_filename(marketplace)
    content_type = get_content_type(marketplace)

    return Response(
        content=job["file_bytes"],
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Products-Total": str(job["total"]),
            "X-Products-Converted": str(job["converted"]),
        },
    )


# ── Allegro API (OAuth, no scraping) ─────────────────────────────────────

@router.get("/allegro-offers", response_model=StoreUrlsResponse)
@limiter.limit("5/minute")
async def get_allegro_offers(
    request: Request,
    db: Session = Depends(get_db),
):
    """Fetch seller's offers via Allegro REST API (requires OAuth connection).

    WHY separate from store-urls: This uses official API (free, fast),
    while store-urls uses web scraping (paid, slower). Both return
    the same response format for frontend compatibility.
    """
    result = await fetch_seller_offers(db)
    return StoreUrlsResponse(**result)


@router.get("/allegro-offer-debug/{offer_id}")
async def debug_allegro_offer(offer_id: str, db: Session = Depends(get_db)):
    """TEMPORARY: Debug Allegro API response for a single offer.
    TODO: Remove after testing.
    """
    from services.allegro_api import fetch_offer_details, get_access_token
    token = await get_access_token(db)
    if not token:
        return {"error": "No Allegro token"}
    result = await fetch_offer_details(offer_id, token)
    return result
