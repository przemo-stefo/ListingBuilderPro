# backend/api/allegro_routes.py
# Purpose: Allegro marketplace publishing — update existing offers via REST API
# NOT for: OAuth flow (oauth_routes.py) or fetching offers (allegro_api.py)

import re
import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db
from services.allegro_api import get_access_token, ALLEGRO_API_BASE

logger = structlog.get_logger()

router = APIRouter(prefix="/api/allegro", tags=["allegro"])
limiter = Limiter(key_func=get_remote_address)

OFFER_ID_PATTERN = re.compile(r"^\d{8,14}$")
ALLEGRO_TITLE_MAX = 75


class OfferUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description_html: str = Field(..., min_length=1)


@router.patch("/offer/{offer_id}")
@limiter.limit("5/minute")
async def update_allegro_offer(
    request: Request,
    offer_id: str,
    body: OfferUpdateRequest,
    db: Session = Depends(get_db),
):
    """PATCH an existing Allegro offer — updates title + description only.

    WHY PATCH not PUT: PUT requires ALL fields (price, stock, delivery).
    PATCH updates only the fields we send, avoiding accidental overwrites.
    """
    if not OFFER_ID_PATTERN.match(offer_id):
        raise HTTPException(status_code=400, detail="Nieprawidlowe ID oferty (8-14 cyfr)")

    access_token = await get_access_token(db)
    if not access_token:
        raise HTTPException(status_code=400, detail="Allegro nie jest polaczone. Polacz konto w ustawieniach.")

    # WHY truncate: Optimizer generates up to 200-char titles (Amazon).
    # Allegro limit is 75. Better to truncate gracefully than reject.
    title = body.title[:ALLEGRO_TITLE_MAX]

    # WHY this format: Allegro requires description as sections → items → TEXT
    allegro_payload = {
        "name": title,
        "description": {
            "sections": [
                {"items": [{"type": "TEXT", "content": body.description_html}]}
            ]
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.patch(
                f"{ALLEGRO_API_BASE}/sale/product-offers/{offer_id}",
                json=allegro_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.allegro.public.v1+json",
                    "Content-Type": "application/vnd.allegro.public.v1+json",
                },
            )

        if resp.status_code in (200, 202):
            logger.info("allegro_offer_updated", offer_id=offer_id)
            return {"status": "ok", "offer_id": offer_id}

        # WHY try/except: Allegro may return HTML error pages (502/503)
        try:
            detail = resp.json().get("errors", [{}])[0].get("message", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        logger.error("allegro_offer_update_failed", offer_id=offer_id, status=resp.status_code, detail=detail)
        raise HTTPException(status_code=resp.status_code, detail=f"Allegro API: {detail}")

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Allegro API timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("allegro_offer_update_error", offer_id=offer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Blad aktualizacji: {str(e)}")
