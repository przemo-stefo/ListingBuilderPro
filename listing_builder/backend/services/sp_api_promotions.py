# backend/services/sp_api_promotions.py
# Purpose: Amazon SP-API Coupons v2022-12-01 — create/list/get/delete coupons
# NOT for: Deals or Lightning Deals (separate API)

import httpx
import structlog
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from config import settings
from services.sp_api_auth import get_access_token, credentials_configured
from services.sp_api_catalog import SP_API_BASE_PROD, SP_API_BASE_SANDBOX, MARKETPLACE_IDS

logger = structlog.get_logger()

# WHY: Coupons API uses seller central endpoint, not SP-API base
COUPONS_BASE_PROD = "https://sellingpartnerapi-eu.amazon.com"
COUPONS_BASE_SANDBOX = "https://sandbox.sellingpartnerapi-eu.amazon.com"
COUPONS_PATH = "/coupons/v2022-12-01"


def _base() -> str:
    return COUPONS_BASE_SANDBOX if settings.amazon_sandbox else COUPONS_BASE_PROD


async def create_coupon(
    seller_id: str,
    coupon_data: Dict[str, Any],
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """Create a coupon promotion.

    coupon_data expected keys:
    - asins: List[str] — target ASINs
    - discount_type: "PERCENTAGE" | "FIXED_AMOUNT"
    - discount_value: float (e.g., 15.0 for 15%)
    - budget: float (EUR)
    - start_date: str (ISO 8601)
    - end_date: str (ISO 8601)
    - name: str — internal coupon name
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    body = {
        "marketplaceId": marketplace_id,
        "couponName": coupon_data.get("name", "Auto-generated coupon"),
        "couponType": "SELLER_COUPON",
        "discountType": coupon_data.get("discount_type", "PERCENTAGE"),
        "discountAmount": coupon_data.get("discount_value", 10),
        "budget": {"amount": coupon_data.get("budget", 100), "currencyCode": "EUR"},
        "startDateTime": coupon_data.get("start_date"),
        "endDateTime": coupon_data.get("end_date"),
        "targetProducts": {
            "productTargets": [{"asin": a} for a in coupon_data.get("asins", [])],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_base()}{COUPONS_PATH}/coupons",
                headers=_headers(token),
                json=body,
            )

        if resp.status_code in (200, 201):
            result = resp.json()
            logger.info("sp_api_coupon_created", coupon_id=result.get("couponId"))
            return {"status": "CREATED", "coupon_id": result.get("couponId"), "detail": result}

        return {"error": f"Coupons API error (kod {resp.status_code})", "detail": resp.text[:200]}
    except Exception as e:
        logger.error("sp_api_coupon_create_error", error=str(e)[:100])
        return {"error": f"Błąd Coupons API: {str(e)[:100]}"}


async def list_coupons(
    seller_id: str,
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """List seller's active coupons."""
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_base()}{COUPONS_PATH}/coupons",
                headers=_headers(token),
                params={"marketplaceId": marketplace_id},
            )

        if resp.status_code == 200:
            return resp.json()

        return {"error": f"Coupons list error (kod {resp.status_code})"}
    except Exception as e:
        logger.error("sp_api_coupons_list_error", error=str(e)[:100])
        return {"error": f"Błąd listy kuponów: {str(e)[:100]}"}


async def get_coupon(
    seller_id: str,
    coupon_id: str,
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """Get single coupon details."""
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_base()}{COUPONS_PATH}/coupons/{coupon_id}",
                headers=_headers(token),
            )

        if resp.status_code == 200:
            return resp.json()

        return {"error": f"Coupon get error (kod {resp.status_code})"}
    except Exception as e:
        logger.error("sp_api_coupon_get_error", error=str(e)[:100])
        return {"error": f"Błąd pobrania kuponu: {str(e)[:100]}"}


async def delete_coupon(
    seller_id: str,
    coupon_id: str,
    marketplace: str = "DE",
    db: Optional[Session] = None,
    user_id: str = "",
) -> Dict[str, Any]:
    """Delete (cancel) a coupon."""
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane"}

    try:
        token = await get_access_token(db=db, user_id=user_id)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji: {str(e)[:100]}"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{_base()}{COUPONS_PATH}/coupons/{coupon_id}",
                headers=_headers(token),
            )

        if resp.status_code in (200, 204):
            logger.info("sp_api_coupon_deleted", coupon_id=coupon_id)
            return {"status": "DELETED", "coupon_id": coupon_id}

        return {"error": f"Coupon delete error (kod {resp.status_code})"}
    except Exception as e:
        logger.error("sp_api_coupon_delete_error", error=str(e)[:100])
        return {"error": f"Błąd usunięcia kuponu: {str(e)[:100]}"}


def _headers(token: str) -> Dict[str, str]:
    return {"x-amz-access-token": token, "Content-Type": "application/json"}
