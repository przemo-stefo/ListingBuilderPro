# backend/api/converter_routes.py
# Purpose: API endpoints for Allegro→Marketplace conversion pipeline
# NOT for: Business logic (that's in services/converter/)

import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

import structlog

from config import settings
from services.scraper.allegro_scraper import (
    scrape_allegro_product,
    scrape_allegro_batch,
    AllegroProduct,
)
from services.converter.ai_translator import AITranslator
from services.converter.converter_service import (
    convert_product,
    convert_batch,
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
            if "allegro.pl" not in url:
                raise ValueError(f"Not an Allegro URL: {url}")
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
        return v


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
async def scrape_allegro(request: ScrapeRequest):
    """Scrape product data from Allegro URLs.

    Returns structured product data (title, EAN, description, images,
    parameters) for each URL. Use this to preview scraped data before
    converting to a marketplace template.
    """
    logger.info("scrape_request", urls_count=len(request.urls))

    products = await scrape_allegro_batch(request.urls, delay=request.delay)

    succeeded = sum(1 for p in products if not p.error)

    return ScrapeResponse(
        total=len(products),
        succeeded=succeeded,
        failed=len(products) - succeeded,
        products=[p.to_dict() for p in products],
    )


@router.post("/convert", response_model=ConvertResponse)
async def convert_to_marketplace(request: ConvertRequest):
    """Full pipeline: Scrape Allegro → Translate → Map → Return JSON.

    Use this endpoint to preview converted data before downloading
    the template file. Returns all mapped fields and warnings.
    """
    logger.info(
        "convert_request",
        urls_count=len(request.urls),
        marketplace=request.marketplace,
    )

    # Step 1: Scrape
    scraped = await scrape_allegro_batch(request.urls, delay=request.delay)

    # Step 2: Initialize AI translator
    translator = AITranslator(groq_api_key=settings.groq_api_key)

    # Step 3: Convert
    converted = convert_batch(
        products=scraped,
        marketplace=request.marketplace,
        translator=translator,
        gpsr_data=request.gpsr_data.model_dump(),
        eur_rate=request.eur_rate,
    )

    succeeded = sum(1 for c in converted if not c.error)
    all_warnings = []
    for c in converted:
        all_warnings.extend(c.warnings)

    return ConvertResponse(
        total=len(converted),
        succeeded=succeeded,
        failed=len(converted) - succeeded,
        marketplace=request.marketplace,
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
async def download_template(request: ConvertRequest):
    """Full pipeline: Scrape → Translate → Map → Download CSV/TSV file.

    Returns a downloadable file:
    - Amazon: Tab-separated .tsv (flat file format)
    - eBay: Comma-separated .csv
    - Kaufland: Semicolon-separated .csv (UTF-8-BOM)
    """
    logger.info(
        "download_request",
        urls_count=len(request.urls),
        marketplace=request.marketplace,
    )

    # Step 1: Scrape
    scraped = await scrape_allegro_batch(request.urls, delay=request.delay)

    # Step 2: Translate + Convert
    translator = AITranslator(groq_api_key=settings.groq_api_key)
    converted = convert_batch(
        products=scraped,
        marketplace=request.marketplace,
        translator=translator,
        gpsr_data=request.gpsr_data.model_dump(),
        eur_rate=request.eur_rate,
    )

    # Step 3: Generate file
    file_bytes = generate_template(converted, request.marketplace)
    filename = get_filename(request.marketplace)
    content_type = get_content_type(request.marketplace)

    succeeded = sum(1 for c in converted if not c.error)
    logger.info("download_generated", marketplace=request.marketplace, products=succeeded)

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
