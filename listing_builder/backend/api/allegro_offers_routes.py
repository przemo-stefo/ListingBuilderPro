# backend/api/allegro_offers_routes.py
# Purpose: Allegro Offers Manager — list, edit, bulk status/price change via REST API
# NOT for: OAuth flow (oauth_routes.py) or single-offer publishing (allegro_routes.py)

import re
import uuid
import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db
from services.allegro_api import get_access_token, fetch_offer_details, ALLEGRO_API_BASE

logger = structlog.get_logger()

router = APIRouter(prefix="/api/allegro/offers", tags=["allegro-offers"])
limiter = Limiter(key_func=get_remote_address)

OFFER_ID_PATTERN = re.compile(r"^\d{8,14}$")
PRICE_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")


# --- Request/Response schemas ---

class OfferPriceUpdate(BaseModel):
    amount: str = Field(..., min_length=1, pattern=r"^\d+(\.\d{1,2})?$")
    currency: Literal["PLN", "EUR", "CZK", "USD"] = "PLN"


# WHY renamed: allegro_routes.py already has OfferUpdateRequest — avoids OpenAPI schema collision
class OfferManagerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=75)
    price: Optional[OfferPriceUpdate] = None
    description_html: Optional[str] = Field(None, max_length=50000)


class BulkStatusRequest(BaseModel):
    offer_ids: List[str] = Field(..., min_length=1, max_length=1000)
    action: Literal["ACTIVATE", "END"]

    @validator("offer_ids", each_item=True)
    def validate_offer_id(cls, v):
        if not OFFER_ID_PATTERN.match(v):
            raise ValueError(f"Nieprawidłowe ID oferty: {v} (wymagane 8-14 cyfr)")
        return v


class BulkPriceChange(BaseModel):
    offer_id: str = Field(..., pattern=r"^\d{8,14}$")
    price: str = Field(..., min_length=1, pattern=r"^\d+(\.\d{1,2})?$")
    currency: Literal["PLN", "EUR", "CZK", "USD"] = "PLN"


class BulkPriceRequest(BaseModel):
    changes: List[BulkPriceChange] = Field(..., min_length=1, max_length=1000)


# --- Helpers ---

def _allegro_headers(access_token: str, with_content_type: bool = True) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
    }
    # WHY: GET requests shouldn't send Content-Type (no body)
    if with_content_type:
        headers["Content-Type"] = "application/vnd.allegro.public.v1+json"
    return headers


async def _require_token(db: Session) -> str:
    """Get valid Allegro token or raise 400."""
    token = await get_access_token(db)
    if not token:
        raise HTTPException(status_code=400, detail="Allegro nie jest połączone. Połącz konto w ustawieniach.")
    return token


def _extract_allegro_error(resp: httpx.Response) -> str:
    """Extract readable error from Allegro API response."""
    try:
        errors = resp.json().get("errors", [])
        if errors and isinstance(errors[0], dict):
            return errors[0].get("message", resp.text[:200])
        return resp.text[:200]
    except Exception:
        return resp.text[:200]


# --- Endpoints ---

@router.get("")
@limiter.limit("10/minute")
async def list_offers(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[Literal["ACTIVE", "INACTIVE", "ENDED"]] = None,
    search: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    """List seller's offers from Allegro with pagination and filtering."""
    access_token = await _require_token(db)

    params: dict = {
        "limit": limit,
        "offset": offset,
        "sort": "-publication.startedAt",
    }

    if status:
        params["publication.status"] = status

    if search:
        params["searchValue"] = search

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/sale/offers",
                params=params,
                headers=_allegro_headers(access_token, with_content_type=False),
            )

        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Token Allegro wygasł. Połącz ponownie.")

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Allegro API: {_extract_allegro_error(resp)}")

        data = resp.json()
        offers = []
        for o in data.get("offers", []):
            price_data = o.get("sellingMode", {}).get("price", {})
            stock_data = o.get("stock", {})
            primary_image = o.get("primaryImage", {})

            offers.append({
                "id": o.get("id", ""),
                "name": o.get("name", ""),
                "price": {
                    "amount": str(price_data.get("amount", "")),
                    "currency": price_data.get("currency", "PLN"),
                },
                "stock": {"available": stock_data.get("available", 0)},
                "status": o.get("publication", {}).get("status", "UNKNOWN"),
                "image": primary_image.get("url", "") if isinstance(primary_image, dict) else "",
                "category": o.get("category", {}).get("id", ""),
            })

        return {"offers": offers, "total": data.get("totalCount", 0)}

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Allegro API timeout")
    except Exception as e:
        logger.error("allegro_list_offers_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd pobierania ofert")


@router.get("/{offer_id}")
@limiter.limit("15/minute")
async def get_offer_detail(
    request: Request,
    offer_id: str,
    db: Session = Depends(get_db),
):
    """Get full details of a single offer. Reuses existing fetch_offer_details()."""
    if not OFFER_ID_PATTERN.match(offer_id):
        raise HTTPException(status_code=400, detail="Nieprawidłowe ID oferty (8-14 cyfr)")

    access_token = await _require_token(db)
    result = await fetch_offer_details(offer_id, access_token)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.patch("/{offer_id}")
@limiter.limit("10/minute")
async def update_offer(
    request: Request,
    offer_id: str,
    body: OfferManagerUpdateRequest,
    db: Session = Depends(get_db),
):
    """Partial update of a single offer — name, price, description."""
    if not OFFER_ID_PATTERN.match(offer_id):
        raise HTTPException(status_code=400, detail="Nieprawidłowe ID oferty (8-14 cyfr)")

    access_token = await _require_token(db)

    # WHY: Build payload with only the fields the user wants to change
    payload: dict = {}

    if body.name is not None:
        payload["name"] = body.name

    if body.price is not None:
        payload["sellingMode"] = {
            "price": {"amount": body.price.amount, "currency": body.price.currency}
        }

    if body.description_html is not None:
        payload["description"] = {
            "sections": [{"items": [{"type": "TEXT", "content": body.description_html}]}]
        }

    if not payload:
        raise HTTPException(status_code=400, detail="Brak pól do aktualizacji")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.patch(
                f"{ALLEGRO_API_BASE}/sale/product-offers/{offer_id}",
                json=payload,
                headers=_allegro_headers(access_token),
            )

        if resp.status_code in (200, 202):
            logger.info("allegro_offer_updated", offer_id=offer_id, fields=list(payload.keys()))
            return {"status": "ok", "offer_id": offer_id}

        detail = _extract_allegro_error(resp)
        logger.error("allegro_offer_update_failed", offer_id=offer_id, status=resp.status_code, detail=detail)
        raise HTTPException(status_code=resp.status_code, detail=f"Allegro API: {detail}")

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Allegro API timeout")
    except Exception as e:
        logger.error("allegro_offer_update_error", offer_id=offer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Błąd aktualizacji oferty")


@router.post("/bulk-status")
@limiter.limit("5/minute")
async def bulk_change_status(
    request: Request,
    body: BulkStatusRequest,
    db: Session = Depends(get_db),
):
    """Bulk ACTIVATE or END offers. Allegro processes this async via command ID."""
    access_token = await _require_token(db)

    # WHY: Allegro requires client-generated UUID as command ID (idempotency key)
    command_id = str(uuid.uuid4())

    payload = {
        "offerCriteria": [{"offers": [{"id": oid} for oid in body.offer_ids], "type": "CONTAINS_OFFERS"}],
        "publication": {"action": body.action},
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"{ALLEGRO_API_BASE}/sale/offer-publication-commands/{command_id}",
                json=payload,
                headers=_allegro_headers(access_token),
            )

        if resp.status_code in (200, 201):
            logger.info("allegro_bulk_status", command_id=command_id, action=body.action, count=len(body.offer_ids))
            return {"command_id": command_id, "status": "accepted", "count": len(body.offer_ids)}

        detail = _extract_allegro_error(resp)
        logger.error("allegro_bulk_status_failed", status=resp.status_code, detail=detail)
        raise HTTPException(status_code=resp.status_code, detail=f"Allegro API: {detail}")

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Allegro API timeout")
    except Exception as e:
        logger.error("allegro_bulk_status_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd zmiany statusu")


@router.post("/bulk-price")
@limiter.limit("5/minute")
async def bulk_change_price(
    request: Request,
    body: BulkPriceRequest,
    db: Session = Depends(get_db),
):
    """Bulk price change for multiple offers. Allegro processes async."""
    access_token = await _require_token(db)

    command_id = str(uuid.uuid4())

    # WHY: Allegro PUT /sale/offer-price-change-commands expects FIXED_PRICE
    # with fixedPrice per offer inside offerCriteria
    payload = {
        "modification": {"type": "FIXED_PRICE"},
        "offerCriteria": [
            {
                "offers": [
                    {
                        "id": c.offer_id,
                        "fixedPrice": {"amount": c.price, "currency": c.currency},
                    }
                    for c in body.changes
                ],
                "type": "CONTAINS_OFFERS",
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"{ALLEGRO_API_BASE}/sale/offer-price-change-commands/{command_id}",
                json=payload,
                headers=_allegro_headers(access_token),
            )

        if resp.status_code in (200, 201):
            logger.info("allegro_bulk_price", command_id=command_id, count=len(body.changes))
            return {"command_id": command_id, "status": "accepted", "count": len(body.changes)}

        detail = _extract_allegro_error(resp)
        logger.error("allegro_bulk_price_failed", status=resp.status_code, detail=detail)
        raise HTTPException(status_code=resp.status_code, detail=f"Allegro API: {detail}")

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Allegro API timeout")
    except Exception as e:
        logger.error("allegro_bulk_price_error", error=str(e))
        raise HTTPException(status_code=500, detail="Błąd zmiany ceny")
