# backend/services/sp_api_listings.py
# Purpose: Amazon SP-API Listings Items v2021-08-01 — get/put/patch listings
# NOT for: Catalog reads (sp_api_catalog) or token management (sp_api_auth)

import httpx
import structlog
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from config import settings
from services.sp_api_auth import get_access_token, credentials_configured
from services.sp_api_catalog import SP_API_BASE_PROD, SP_API_BASE_SANDBOX, MARKETPLACE_IDS

logger = structlog.get_logger()

LISTINGS_API_VERSION = "2021-08-01"


def _base_url() -> str:
    return SP_API_BASE_SANDBOX if settings.amazon_sandbox else SP_API_BASE_PROD


async def get_listing(
    seller_id: str,
    sku: str,
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """GET listing by seller_id + SKU.

    WHY separate from catalog: Catalog is read-only product data.
    Listings API gives seller-specific listing with issues, status, offers.
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    url = f"{_base_url()}/listings/{LISTINGS_API_VERSION}/items/{seller_id}/{sku}"
    params = {"marketplaceIds": marketplace_id, "includedData": "summaries,attributes,issues,offers"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=_headers(token), params=params)

        if resp.status_code != 200:
            return {"error": f"Listings API error (kod {resp.status_code})"}

        return resp.json()
    except Exception as e:
        logger.error("sp_api_listings_get_error", error=str(e)[:100])
        return {"error": f"Błąd Listings API: {str(e)[:100]}"}


async def put_listing(
    seller_id: str,
    sku: str,
    product_type: str,
    attributes: Dict[str, Any],
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """PUT (create/replace) listing via Listings Items API.

    WHY PUT not POST: SP-API uses PUT for create-or-replace semantics.
    Product type + attributes define the full listing.
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    url = f"{_base_url()}/listings/{LISTINGS_API_VERSION}/items/{seller_id}/{sku}"
    params = {"marketplaceIds": marketplace_id}
    body = {
        "productType": product_type,
        "requirements": "LISTING",
        "attributes": attributes,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.put(url, headers=_headers(token), params=params, json=body)

        if resp.status_code in (200, 202):
            logger.info("sp_api_listing_put_ok", seller_id=seller_id, sku=sku)
            return {"status": "ACCEPTED", "sku": sku, "issues": resp.json().get("issues", [])}

        return {"error": f"Listings PUT failed (kod {resp.status_code})", "detail": resp.text[:200]}
    except Exception as e:
        logger.error("sp_api_listings_put_error", error=str(e)[:100])
        return {"error": f"Błąd Listings API PUT: {str(e)[:100]}"}


async def patch_listing(
    seller_id: str,
    sku: str,
    product_type: str,
    patches: List[Dict[str, Any]],
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """PATCH listing with JSON Patch operations.

    WHY PATCH: Partial updates — change title without re-submitting all attributes.
    patches format: [{"op": "replace", "path": "/attributes/title", "value": [...]}]
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    url = f"{_base_url()}/listings/{LISTINGS_API_VERSION}/items/{seller_id}/{sku}"
    params = {"marketplaceIds": marketplace_id}
    body = {"productType": product_type, "patches": patches}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.patch(url, headers=_headers(token), params=params, json=body)

        if resp.status_code in (200, 202):
            logger.info("sp_api_listing_patch_ok", seller_id=seller_id, sku=sku)
            return {"status": "ACCEPTED", "sku": sku, "issues": resp.json().get("issues", [])}

        return {"error": f"Listings PATCH failed (kod {resp.status_code})"}
    except Exception as e:
        logger.error("sp_api_listings_patch_error", error=str(e)[:100])
        return {"error": f"Błąd Listings API PATCH: {str(e)[:100]}"}


def _headers(token: str) -> Dict[str, str]:
    return {"x-amz-access-token": token, "Content-Type": "application/json"}
