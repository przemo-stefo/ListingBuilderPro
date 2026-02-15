# backend/services/converter/converter_service.py
# Purpose: Orchestrate Allegro→Marketplace conversion (scrape→translate→map→generate)
# NOT for: Individual scraping, AI calls, or template file I/O

import asyncio
import random
import re
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import structlog

from services.scraper.allegro_scraper import AllegroProduct, scrape_allegro_product
from services.converter.ai_translator import (
    AITranslator,
    translate_color,
    translate_material,
    translate_gender,
    translate_condition,
)
from services.converter.field_mapping import (
    CONDITION_ALLEGRO_TO_EBAY,
    GENDER_ALLEGRO_TO_MARKETPLACE,
)

logger = structlog.get_logger()


@dataclass
class ConvertedProduct:
    """Product data mapped and translated for a specific marketplace."""

    source_url: str = ""
    source_id: str = ""
    marketplace: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ── Value parsers ─────────────────────────────────────────────────────────

def parse_weight(weight_str: str) -> str:
    """Parse Allegro weight format ('0,500 kg', '500 g') to decimal kg."""
    if not weight_str:
        return ""
    weight_str = weight_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(kg|g)', weight_str)
    if not match:
        return weight_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "g":
        value = value / 1000
    return f"{value:.3f}"


def parse_dimension_mm(dim_str: str) -> str:
    """Parse Allegro dimension to millimeters (Kaufland format)."""
    if not dim_str:
        return ""
    dim_str = dim_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(mm|cm|m)', dim_str)
    if not match:
        return dim_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "cm":
        value = value * 10
    elif unit == "m":
        value = value * 1000
    return f"{value:.0f}"


def parse_dimension_cm(dim_str: str) -> str:
    """Parse Allegro dimension to centimeters (Amazon format)."""
    if not dim_str:
        return ""
    dim_str = dim_str.lower().strip()
    match = re.search(r'([\d,\.]+)\s*(mm|cm|m)', dim_str)
    if not match:
        return dim_str
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit == "mm":
        value = value / 10
    elif unit == "m":
        value = value * 100
    return f"{value:.1f}"


def convert_pln_to_eur(pln_price: str, rate: float = 0.23) -> str:
    """Convert PLN price to EUR. Default rate ~0.23 (1 PLN ≈ 0.23 EUR).

    Rate should be updated from a live source in production.
    """
    try:
        value = float(pln_price.replace(",", ".").strip())
        eur = value * rate
        return f"{eur:.2f}"
    except (ValueError, AttributeError):
        return pln_price


def get_param(product: AllegroProduct, *keys: str) -> str:
    """Get parameter value by trying multiple Polish key variants."""
    for key in keys:
        # Exact match
        if key in product.parameters:
            return product.parameters[key]
        # Case-insensitive match
        for pk, pv in product.parameters.items():
            if key.lower() in pk.lower():
                return pv
    return ""


# ── Marketplace converters ────────────────────────────────────────────────

def convert_to_amazon(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Map scraped Allegro product to Amazon.de flat file fields.

    Args:
        product: Scraped Allegro data
        ai: AI-translated content from AITranslator.translate_product_batch()
        gpsr_data: User-provided GPSR/manufacturer data (reused across products)
        eur_rate: PLN→EUR exchange rate
    """
    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="amazon",
    )

    f = result.fields  # Shorthand

    # Identity
    f["item_sku"] = f"ALG-{product.source_id}"
    f["update_delete"] = "Update"
    f["external_product_id"] = product.ean
    f["external_product_id_type"] = "EAN" if product.ean else ""

    # Title + Description (AI-translated)
    f["item_name"] = ai.get("title_de", product.title)
    f["product_description"] = ai.get("description_de", "")

    # Bullet points (AI-generated, Amazon only)
    bullets = ai.get("bullet_points", [""] * 5)
    for i, bp in enumerate(bullets[:5]):
        f[f"bullet_point{i+1}"] = bp

    # Search keywords
    f["generic_keywords"] = ai.get("search_keywords", "")

    # Brand / Manufacturer
    f["brand_name"] = product.brand or get_param(product, "Marka")
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")
    f["part_number"] = get_param(product, "MPN", "Numer producenta")
    f["model"] = get_param(product, "Model")

    # GPSR (user-provided, same for all products from same manufacturer)
    f["manufacturer_contact_information"] = gpsr_data.get("manufacturer_contact", "")
    f["country_of_origin"] = gpsr_data.get("country_of_origin", "")
    f["gpsr_safety_attestation"] = gpsr_data.get("safety_attestation", "")

    # Pricing
    f["standard_price"] = convert_pln_to_eur(product.price, eur_rate)
    f["quantity"] = product.quantity or "1"

    # Images
    for i, img_url in enumerate(product.images[:9]):
        if i == 0:
            f["main_image_url"] = img_url
        else:
            f[f"other_image_url{i}"] = img_url

    # Physical attributes
    f["item_weight"] = parse_weight(get_param(product, "Waga"))
    f["item_dimensions_length"] = parse_dimension_cm(get_param(product, "Długość"))
    f["item_dimensions_width"] = parse_dimension_cm(get_param(product, "Szerokość"))
    f["item_dimensions_height"] = parse_dimension_cm(get_param(product, "Wysokość"))

    # Color / Material (lookup first, AI fallback)
    f["color_name"] = ai.get("color_de", "")
    f["material_type"] = ai.get("material_de", "")

    # Size / Gender
    f["size_name"] = get_param(product, "Rozmiar")
    gender = get_param(product, "Płeć")
    f["target_gender"] = translate_gender(gender, "amazon") or ""

    # Language
    f["language_value1"] = "German"

    # Category (user must provide)
    f["recommended_browse_nodes"] = gpsr_data.get("amazon_browse_node", "")
    f["feed_product_type"] = gpsr_data.get("amazon_product_type", "")

    # Warnings for missing required fields
    if not product.ean:
        result.warnings.append("EAN missing — required for Amazon")
    if not f["brand_name"]:
        result.warnings.append("Brand missing — required for Amazon")
    if not f["manufacturer_contact_information"]:
        result.warnings.append("GPSR manufacturer contact missing — provide in settings")
    if not f["recommended_browse_nodes"]:
        result.warnings.append("Amazon browse node missing — select category")

    return result


def convert_to_ebay(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
    eur_rate: float = 0.23,
) -> ConvertedProduct:
    """Map scraped Allegro product to eBay.de bulk listing fields."""

    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="ebay",
    )

    f = result.fields

    # System fields
    f["*Action(SiteID=77)"] = "Add"
    f["Category ID"] = gpsr_data.get("ebay_category_id", "")

    # Title + Description (AI)
    f["Title"] = ai.get("title_de", product.title)[:80]
    f["Description"] = ai.get("description_de", "")

    # Identifiers
    f["Custom label (SKU)"] = f"ALG-{product.source_id}"
    f["Product:EAN"] = product.ean
    f["Product:MPN"] = get_param(product, "MPN", "Numer producenta")

    # Pricing
    f["Start Price"] = convert_pln_to_eur(product.price, eur_rate)
    f["Quantity"] = product.quantity or "1"

    # Condition
    condition = product.condition or get_param(product, "Stan")
    f["Condition ID"] = str(translate_condition(condition) or 1000)

    # Images (pipe-separated for eBay)
    f["PicURL"] = "|".join(product.images[:12]) if product.images else ""

    # Item specifics
    f["C:Marke"] = product.brand or get_param(product, "Marka")
    f["C:Hersteller"] = product.manufacturer or get_param(product, "Producent")
    f["C:Herstellernummer"] = get_param(product, "MPN", "Numer producenta")
    f["C:Farbe"] = ai.get("color_de", "")
    f["C:Material"] = ai.get("material_de", "")
    f["C:Größe"] = get_param(product, "Rozmiar")

    # GPSR manufacturer
    f["Manufacturer Name"] = product.manufacturer or get_param(product, "Producent")
    f["Manufacturer Address Line 1"] = gpsr_data.get("manufacturer_address", "")
    f["Manufacturer City"] = gpsr_data.get("manufacturer_city", "")
    f["Manufacturer Country"] = gpsr_data.get("manufacturer_country", "")

    # GPSR responsible person
    f["Responsible Person 1 Type"] = gpsr_data.get("responsible_person_type", "")
    f["Responsible Person 1 Name"] = gpsr_data.get("responsible_person_name", "")
    f["Responsible Person 1 Address Line 1"] = gpsr_data.get("responsible_person_address", "")
    f["Responsible Person 1 Country"] = gpsr_data.get("responsible_person_country", "")

    # Listing format
    f["Format"] = "FixedPrice"
    f["Duration"] = "GTC"

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — required for eBay")
    if not f["Category ID"]:
        result.warnings.append("eBay Category ID missing — select category")
    if not f["Manufacturer Address Line 1"]:
        result.warnings.append("GPSR manufacturer address missing — provide in settings")

    return result


def convert_to_kaufland(
    product: AllegroProduct,
    ai: Dict,
    gpsr_data: Dict,
) -> ConvertedProduct:
    """Map scraped Allegro product to Kaufland.de CSV fields."""

    result = ConvertedProduct(
        source_url=product.source_url,
        source_id=product.source_id,
        marketplace="kaufland",
    )

    f = result.fields

    # Identity
    f["ean"] = product.ean
    f["locale"] = "de-DE"
    f["category"] = gpsr_data.get("kaufland_category", "")

    # Title + Description (AI)
    f["title"] = ai.get("title_de", product.title)[:120]
    f["short_description"] = ai.get("short_description_de", "")
    f["description"] = ai.get("description_de", "")

    # Manufacturer
    f["manufacturer"] = product.manufacturer or get_param(product, "Producent")
    f["mpn"] = get_param(product, "MPN", "Numer producenta")

    # Images (Kaufland: 4 slots, all same column name "picture")
    for i, img_url in enumerate(product.images[:4]):
        # Kaufland template has 4 columns all named "picture"
        f[f"picture_{i+1}"] = img_url

    # Physical attributes
    f["colour"] = ai.get("color_de", "")
    gender = get_param(product, "Płeć")
    f["target"] = translate_gender(gender, "kaufland") or ""
    f["material_composition"] = ai.get("material_de", "")
    f["weight"] = parse_weight(get_param(product, "Waga"))
    f["quantity"] = product.quantity or "1"
    f["length"] = parse_dimension_mm(get_param(product, "Długość"))
    f["width"] = parse_dimension_mm(get_param(product, "Szerokość"))
    f["height"] = parse_dimension_mm(get_param(product, "Wysokość"))

    # Size (Kaufland splits shoe/clothing — we put in both, user picks)
    size = get_param(product, "Rozmiar")
    f["shoe_size"] = ""
    f["clothing_size"] = size

    # Warnings
    if not product.ean:
        result.warnings.append("EAN missing — required for Kaufland")
    if not f["category"]:
        result.warnings.append("Kaufland category missing — select category (German name)")
    if not f["manufacturer"]:
        result.warnings.append("Manufacturer missing — required for Kaufland")

    return result


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
    else:
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


def create_store_job(urls: List[str], marketplace: str) -> str:
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
    }
    return job_id


def get_store_job(job_id: str) -> Optional[dict]:
    """Get job status by ID."""
    return _store_jobs.get(job_id)


async def process_store_job(
    job_id: str,
    urls: List[str],
    marketplace: str,
    gpsr_data: Dict,
    eur_rate: float,
    groq_api_key: str,
) -> None:
    """Background task: scrape each URL → convert → generate file.

    WHY async: scraping is I/O-bound (HTTP calls), async lets us
    update progress counters between products without blocking.
    """
    from services.converter.template_generator import generate_template

    job = _store_jobs[job_id]
    translator = AITranslator(groq_api_key=groq_api_key)
    converted_products: List[ConvertedProduct] = []

    for i, url in enumerate(urls):
        try:
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

            if i < len(urls) - 1:
                await asyncio.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            job["failed"] += 1
            logger.error("store_job_error", job_id=job_id, url=url[:80], error=str(e))

    if converted_products:
        job["file_bytes"] = generate_template(converted_products, marketplace)

    job["status"] = "done"
    logger.info("store_job_complete", job_id=job_id, total=len(urls),
                converted=len(converted_products), failed=job["failed"])
