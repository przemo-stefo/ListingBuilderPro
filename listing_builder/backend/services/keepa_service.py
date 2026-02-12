# backend/services/keepa_service.py
# Purpose: Keepa API integration — Amazon price history, Buy Box, stock tracking
# NOT for: Direct Amazon SP-API calls or scraping (separate services)

import httpx
import os
import structlog
from typing import Optional

logger = structlog.get_logger()

KEEPA_BASE_URL = "https://api.keepa.com"
KEEPA_API_KEY = os.getenv("KEEPA_API_KEY", "")

# WHY: Keepa domain IDs map to Amazon marketplaces
DOMAIN_MAP = {
    "amazon.com": 1,
    "amazon.co.uk": 2,
    "amazon.de": 3,
    "amazon.fr": 4,
    "amazon.co.jp": 5,
    "amazon.ca": 6,
    "amazon.it": 8,
    "amazon.es": 9,
    "amazon.com.mx": 11,
    "amazon.pl": 15,
    "amazon.nl": 10,
}


async def get_product(asin: str, domain: str = "amazon.de") -> Optional[dict]:
    """Fetch product data from Keepa: prices, Buy Box, rating, stock."""
    if not KEEPA_API_KEY:
        logger.warning("keepa_no_api_key")
        return None

    domain_id = DOMAIN_MAP.get(domain, 3)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{KEEPA_BASE_URL}/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "asin": asin,
                "history": 1,
                "buybox": 1,
                "stock": 1,
                "rating": 1,
                "offers": 20,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("products"):
        logger.info("keepa_product_not_found", asin=asin)
        return None

    product = data["products"][0]
    tokens_used = data.get("tokensConsumed", 0)
    tokens_left = data.get("tokensLeft", 0)
    logger.info("keepa_product_fetched", asin=asin, tokens_used=tokens_used, tokens_left=tokens_left)

    return _parse_product(product)


async def get_products_batch(asins: list[str], domain: str = "amazon.de") -> list[dict]:
    """Fetch up to 100 products in one call (Keepa allows comma-separated ASINs)."""
    if not KEEPA_API_KEY or not asins:
        return []

    # WHY: Keepa max 100 ASINs per request
    asins = asins[:100]
    domain_id = DOMAIN_MAP.get(domain, 3)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{KEEPA_BASE_URL}/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "asin": ",".join(asins),
                "history": 1,
                "buybox": 1,
                "stock": 1,
                "rating": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    products = data.get("products", [])
    logger.info("keepa_batch_fetched", count=len(products), tokens_left=data.get("tokensLeft", 0))

    return [_parse_product(p) for p in products]


async def get_buybox_history(asin: str, domain: str = "amazon.de") -> Optional[dict]:
    """Fetch Buy Box history — who won, at what price, when."""
    if not KEEPA_API_KEY:
        return None

    domain_id = DOMAIN_MAP.get(domain, 3)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{KEEPA_BASE_URL}/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "asin": asin,
                "history": 0,
                "buybox": 1,
                "offers": 20,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("products"):
        return None

    product = data["products"][0]
    return {
        "asin": asin,
        "buybox_seller_id": product.get("buyBoxSellerIdHistory"),
        "buybox_is_amazon": product.get("buyBoxIsFBA"),
        "offer_count": product.get("offerCountFBA", 0) + product.get("offerCountFBM", 0),
        "offers_fba": product.get("offerCountFBA", 0),
        "offers_fbm": product.get("offerCountFBM", 0),
    }


async def check_tokens_left() -> dict:
    """Check remaining Keepa API tokens (rate limit info)."""
    if not KEEPA_API_KEY:
        return {"error": "no_api_key"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{KEEPA_BASE_URL}/token",
            params={"key": KEEPA_API_KEY},
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "tokens_left": data.get("tokensLeft", 0),
        "refill_in": data.get("refillIn", 0),
        "refill_rate": data.get("refillRate", 0),
    }


def _parse_product(product: dict) -> dict:
    """Extract key fields from Keepa's raw product response."""
    csv = product.get("csv", [])

    # WHY: Keepa stores prices in cents, -1 = no data, -2 = out of stock
    current_price = _latest_price(csv[0]) if len(csv) > 0 else None
    buybox_price = _latest_price(csv[18]) if len(csv) > 18 else None

    return {
        "asin": product.get("asin"),
        "title": product.get("title"),
        "brand": product.get("brand"),
        "category": product.get("categoryTree", [{}])[-1].get("name") if product.get("categoryTree") else None,
        "current_price": current_price,
        "buybox_price": buybox_price,
        "sales_rank": product.get("salesRanks", {}).get("current"),
        "rating": (product.get("csv", [[]])[16][-1] / 10) if len(csv) > 16 and csv[16] else None,
        "review_count": product.get("csv", [[]])[17][-1] if len(csv) > 17 and csv[17] else None,
        "is_alive": product.get("isAlive", False),
        "last_update": product.get("lastUpdate"),
        "offers_fba": product.get("offerCountFBA", 0),
        "offers_fbm": product.get("offerCountFBM", 0),
        "image_url": f"https://images-na.ssl-images-amazon.com/images/I/{product.get('imagesCSV', '').split(',')[0]}" if product.get("imagesCSV") else None,
    }


def _latest_price(price_history: list) -> Optional[float]:
    """Get latest price from Keepa price history array (time, value pairs)."""
    if not price_history or len(price_history) < 2:
        return None
    # WHY: Last element is the most recent value, stored in cents
    val = price_history[-1]
    if val < 0:
        return None
    return val / 100.0
