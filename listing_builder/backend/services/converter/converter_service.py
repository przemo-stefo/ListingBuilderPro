# backend/services/converter/converter_service.py
# Purpose: Orchestrate Allegro→Marketplace conversion (scrape→translate→map→generate)
# NOT for: Individual converter functions (marketplace_converters.py), value parsers (converter_helpers.py)

import asyncio
import random
import uuid
from typing import Dict, List, Optional

import structlog

from services.scraper.allegro_scraper import AllegroProduct, scrape_allegro_product
from services.converter.ai_translator import AITranslator

# WHY re-export: Many files import ConvertedProduct etc. from converter_service.
# Keeping re-exports avoids breaking existing imports across the codebase.
from services.converter.converter_helpers import (  # noqa: F401
    ConvertedProduct,
    get_param,
    parse_weight,
    parse_dimension_cm,
    parse_dimension_mm,
    convert_pln_to_eur,
)
from services.converter.marketplace_converters import (
    convert_to_amazon,
    convert_to_ebay,
    convert_to_kaufland,
    convert_to_bol,
    convert_to_rozetka,
)

logger = structlog.get_logger()


# ── Main orchestrator ─────────────────────────────────────────────────────

def convert_product(
    product: AllegroProduct,
    marketplace: str,
    translator: AITranslator,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Convert a single scraped Allegro product to target marketplace format.

    This is the main entry point. Handles:
    1. AI translation (batch, one API call per product)
    2. Field mapping with static lookups
    3. Value transformations (price, weight, dimensions)

    Args:
        product: Scraped AllegroProduct
        marketplace: Target ("amazon", "ebay", "kaufland")
        translator: AITranslator instance
        gpsr_data: User-provided GPSR/manufacturer data
        eur_rate: PLN→EUR exchange rate

    Returns:
        ConvertedProduct with all mapped fields
    """
    if product.error:
        return ConvertedProduct(
            source_url=product.source_url,
            source_id=product.source_id,
            marketplace=marketplace,
            error=f"Skipped — scraping failed: {product.error}",
        )

    # Step 1: AI translation (one batched API call for all text fields)
    logger.info("translating_product", source_id=product.source_id, marketplace=marketplace)
    ai_content = translator.translate_product_batch(
        title=product.title,
        description=product.description,
        parameters=product.parameters,
        marketplace=marketplace,
    )

    # Step 2: Map to marketplace-specific fields
    converters = {
        "amazon": convert_to_amazon,
        "ebay": convert_to_ebay,
        "kaufland": convert_to_kaufland,
        "bol": convert_to_bol,
        "rozetka": convert_to_rozetka,
    }

    converter_fn = converters.get(marketplace)
    if not converter_fn:
        return ConvertedProduct(
            source_url=product.source_url,
            marketplace=marketplace,
            error=f"Unknown marketplace: {marketplace}",
        )

    if marketplace == "kaufland":
        result = converter_fn(product, ai_content, gpsr_data)
    elif marketplace == "rozetka":
        # WHY: Rozetka uses UAH, not EUR — default rate ~9.5 PLN→UAH
        result = converter_fn(product, ai_content, gpsr_data)
    else:
        # WHY: amazon, ebay, bol all need eur_rate for PLN→EUR conversion
        result = converter_fn(product, ai_content, gpsr_data, eur_rate)

    logger.info(
        "product_converted",
        source_id=product.source_id,
        marketplace=marketplace,
        fields_count=len(result.fields),
        warnings_count=len(result.warnings),
    )

    return result


def convert_batch(
    products: List[AllegroProduct],
    marketplace: str,
    translator: AITranslator,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> List[ConvertedProduct]:
    """Convert multiple scraped products to target marketplace format."""
    results = []
    for i, product in enumerate(products):
        logger.info("converting_batch", progress=f"{i+1}/{len(products)}")
        converted = convert_product(product, marketplace, translator, gpsr_data, eur_rate)
        results.append(converted)
    return results


# ── Store job processing (async, in-memory) ──────────────────────────────
# WHY in-memory: Render free tier = 1 worker, no need for Redis/DB.
# Jobs auto-expire after processing — dict stays small.

_store_jobs: Dict[str, dict] = {}


def create_store_job(urls: List[str], marketplace: str, user_id: str = "default") -> str:
    """Create a new store conversion job, return job_id."""
    job_id = str(uuid.uuid4())
    _store_jobs[job_id] = {
        "status": "processing",
        "total": len(urls),
        "scraped": 0,
        "converted": 0,
        "failed": 0,
        "marketplace": marketplace,
        "file_bytes": None,
        "user_id": user_id,
    }
    return job_id


def get_store_job(job_id: str, user_id: str = None) -> Optional[dict]:
    """Get job status by ID. If user_id provided, verify ownership."""
    job = _store_jobs.get(job_id)
    if job and user_id and job.get("user_id") != user_id:
        return None
    return job


async def process_store_job(
    job_id: str,
    urls: List[str],
    marketplace: str,
    gpsr_data: Dict,
    eur_rate: float,
    groq_api_key: str,
    allegro_token: Optional[str] = None,
) -> None:
    """Background task: fetch product data → convert → generate file.

    WHY Allegro API first: Free, fast (<1s vs 5s), structured JSON,
    no Scrape.do limits. Falls back to scraper only if no OAuth token.
    """
    from services.converter.template_generator import generate_template
    from services.allegro_api import fetch_offer_details

    job = _store_jobs[job_id]
    translator = AITranslator(groq_api_key=groq_api_key)
    converted_products: List[ConvertedProduct] = []

    for i, url in enumerate(urls):
        try:
            offer_id = re.search(r'(\d{8,14})$', url.split("?")[0].rstrip("/"))
            oid = offer_id.group(1) if offer_id else ""

            # WHY: Seller API → Scrape.do fallback
            # Public API (Client Credentials) doesn't work — Allegro requires verified app
            if allegro_token and oid:
                data = await fetch_offer_details(oid, allegro_token)
                if not data.get("error"):
                    product = AllegroProduct(**{
                        k: v for k, v in data.items() if k != "error"
                    })
                else:
                    product = await scrape_allegro_product(url)
            else:
                product = await scrape_allegro_product(url)

            job["scraped"] = i + 1

            if product.error:
                job["failed"] += 1
                logger.warning("store_job_skip", job_id=job_id, url=url[:80],
                               error=product.error)
                continue

            result = convert_product(product, marketplace, translator, gpsr_data, eur_rate)
            if result.error:
                job["failed"] += 1
            else:
                converted_products.append(result)
                job["converted"] = len(converted_products)

            # WHY shorter delay for API: no anti-bot throttling needed
            if i < len(urls) - 1:
                delay = random.uniform(0.5, 1.5) if allegro_token else random.uniform(2.0, 4.0)
                await asyncio.sleep(delay)

        except Exception as e:
            job["failed"] += 1
            logger.error("store_job_error", job_id=job_id, url=url[:80], error=str(e))

    if converted_products:
        job["file_bytes"] = generate_template(converted_products, marketplace)

    job["status"] = "done"
    logger.info("store_job_complete", job_id=job_id, total=len(urls),
                converted=len(converted_products), failed=job["failed"],
                method="api" if allegro_token else "scraper")
