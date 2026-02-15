# backend/services/allegro_api.py
# Purpose: Allegro REST API client — fetch seller's offers using stored OAuth token
# NOT for: OAuth flow (that's oauth_service.py) or HTML scraping (allegro_scraper.py)

import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Dict
from sqlalchemy.orm import Session

from config import settings
from models.oauth_connection import OAuthConnection

logger = structlog.get_logger()

ALLEGRO_API_BASE = "https://api.allegro.pl"
ALLEGRO_TOKEN_URL = "https://allegro.pl/auth/oauth/token"


async def _refresh_token_if_needed(conn: OAuthConnection, db: Session) -> bool:
    """Refresh Allegro access token if expired.

    WHY auto-refresh: Allegro tokens expire in ~12h. Using refresh_token
    means the user doesn't have to re-authorize every time.
    """
    if conn.token_expires_at and conn.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        return True

    if not conn.refresh_token:
        logger.warning("allegro_no_refresh_token")
        return False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                ALLEGRO_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": conn.refresh_token,
                },
                auth=(settings.allegro_client_id, settings.allegro_client_secret),
            )

        if resp.status_code != 200:
            logger.error("allegro_token_refresh_failed", status=resp.status_code)
            return False

        data = resp.json()
        conn.access_token = data["access_token"]
        conn.refresh_token = data.get("refresh_token", conn.refresh_token)
        conn.token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=data.get("expires_in", 43200)
        )
        conn.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("allegro_token_refreshed")
        return True

    except Exception as e:
        logger.error("allegro_token_refresh_error", error=str(e))
        return False


async def fetch_seller_offers(db: Session) -> Dict:
    """Fetch all active offers from connected Allegro seller account.

    WHY API not scraping: Official API is free, fast (<1s vs 5s/product),
    structured JSON (no HTML parsing), and never blocked by DataDome.

    Returns same format as scrape_allegro_store_urls() for compatibility
    with existing converter pipeline.
    """
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == "default",
        OAuthConnection.marketplace == "allegro",
    ).first()

    if not conn or conn.status != "active":
        return {"store_name": "", "urls": [], "total": 0,
                "error": "Allegro nie jest połączone. Kliknij 'Połącz z Allegro'.",
                "capped": False}

    if not await _refresh_token_if_needed(conn, db):
        return {"store_name": "", "urls": [], "total": 0,
                "error": "Token Allegro wygasł. Połącz ponownie.",
                "capped": False}

    all_urls = []
    offset = 0
    limit = 1000

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                resp = await client.get(
                    f"{ALLEGRO_API_BASE}/sale/offers",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "publication.status": "ACTIVE",
                        "sort": "-publication.startedAt",
                    },
                    headers={
                        "Authorization": f"Bearer {conn.access_token}",
                        "Accept": "application/vnd.allegro.public.v1+json",
                    },
                )

                if resp.status_code == 401:
                    return {"store_name": "", "urls": [], "total": 0,
                            "error": "Token Allegro wygasł. Połącz ponownie.",
                            "capped": False}

                if resp.status_code != 200:
                    return {"store_name": "", "urls": [], "total": 0,
                            "error": f"Allegro API error: {resp.status_code}",
                            "capped": False}

                data = resp.json()
                offers = data.get("offers", [])

                for offer in offers:
                    offer_id = offer.get("id", "")
                    if offer_id:
                        # WHY /oferta/{id}: Allegro redirects to canonical URL with slug
                        all_urls.append(f"https://allegro.pl/oferta/{offer_id}")

                total_count = data.get("totalCount", 0)
                offset += limit

                if offset >= total_count or not offers:
                    break

        seller_name = conn.seller_name or "Twoje konto Allegro"
        logger.info("allegro_api_offers_fetched", total=len(all_urls))

        return {
            "store_name": seller_name,
            "urls": all_urls,
            "total": len(all_urls),
            "error": None,
            "capped": False,
        }

    except httpx.TimeoutException:
        return {"store_name": "", "urls": [], "total": 0,
                "error": "Allegro API timeout", "capped": False}
    except Exception as e:
        logger.error("allegro_api_error", error=str(e))
        return {"store_name": "", "urls": [], "total": 0,
                "error": f"Allegro API error: {str(e)}", "capped": False}
