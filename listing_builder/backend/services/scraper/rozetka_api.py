# backend/services/scraper/rozetka_api.py
# Purpose: Direct HTTP calls to Rozetka open API (no auth, no Cloudflare)
# NOT for: Scrape.do integration, HTML parsing, or orchestration

import asyncio
from typing import Dict

import httpx
import structlog

logger = structlog.get_logger()

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# WHY: Rozetka open API base — no auth, no Cloudflare (verified 2026-02-28)
_PRODUCT_API = "https://product-api.rozetka.com.ua/v4/goods"


def _api_params(product_id: str) -> tuple[dict, dict]:
    """Build query params and headers for Rozetka open API calls."""
    params = {
        "goodsId": product_id,
        "front-type": "xl",
        "country": "UA",
        "lang": "ua",
    }
    return params, {"User-Agent": _UA}


async def _fetch_description(client: httpx.AsyncClient, product_id: str) -> str:
    """Fetch HTML description from Rozetka open API."""
    params, headers = _api_params(product_id)
    try:
        resp = await client.get(
            f"{_PRODUCT_API}/get-goods-description",
            params=params, headers=headers,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("text", "")
    except Exception as e:
        logger.warning("rozetka_api_description_failed", product_id=product_id, error=str(e))
    return ""


async def _fetch_specs(client: httpx.AsyncClient, product_id: str) -> Dict[str, str]:
    """Fetch product specs/characteristics from Rozetka open API."""
    params, headers = _api_params(product_id)
    try:
        resp = await client.get(
            f"{_PRODUCT_API}/get-characteristic",
            params=params, headers=headers,
        )
        if resp.status_code == 200:
            result: Dict[str, str] = {}
            for group in resp.json().get("data", []):
                for opt in group.get("options", []):
                    key = opt.get("title", "")
                    values = [v.get("title", "") for v in opt.get("values", [])]
                    if key and values:
                        result[key] = ", ".join(values)
            return result
    except Exception as e:
        logger.warning("rozetka_api_specs_failed", product_id=product_id, error=str(e))
    return {}


async def fetch_rozetka_api(product_id: str) -> dict:
    """Fetch description + specs from Rozetka open API (no auth needed).

    WHY separate: These endpoints have no Cloudflare, so we always call them directly.
    WHY gather: Two independent API calls — parallel saves ~1-2s.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        description, parameters = await asyncio.gather(
            _fetch_description(client, product_id),
            _fetch_specs(client, product_id),
        )
    return {"description": description, "parameters": parameters}
