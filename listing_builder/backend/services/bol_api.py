# backend/services/bol_api.py
# Purpose: BOL.com Retailer API v10 client — fetch offers via Client Credentials
# NOT for: OAuth browser redirect flow (BOL uses server-to-server only)

import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from models.oauth_connection import OAuthConnection

logger = structlog.get_logger()

BOL_TOKEN_URL = "https://login.bol.com/token"
BOL_API_BASE = "https://api.bol.com/retailer"
BOL_ACCEPT = "application/vnd.retailer.v10+json"


async def validate_bol_credentials(client_id: str, client_secret: str) -> Dict:
    """Test BOL.com credentials by fetching a token.

    WHY separate from get_bol_token: Returns structured result with error message
    for the connect flow, not just None.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BOL_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
            )

        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "token": data.get("access_token"),
                "expires_in": data.get("expires_in", 300),
            }

        logger.warning("bol_credentials_invalid", status=resp.status_code)
        return {"valid": False, "error": f"BOL.com zwrócił {resp.status_code} — sprawdź client_id/secret"}

    except httpx.TimeoutException:
        return {"valid": False, "error": "BOL.com timeout — spróbuj ponownie"}
    except Exception as e:
        return {"valid": False, "error": f"Błąd połączenia: {str(e)}"}


async def _get_fresh_token(conn: OAuthConnection, db: Session) -> Optional[str]:
    """Get valid BOL token, refreshing if expired.

    WHY 60s buffer: BOL tokens last ~5 min. Refresh early to avoid
    mid-request expiry. Allegro uses 5 min buffer (12h token) — we use
    60s because BOL token is much shorter-lived.
    """
    now = datetime.now(timezone.utc)
    if (conn.access_token
            and conn.token_expires_at
            and conn.token_expires_at > now + timedelta(seconds=60)):
        return conn.access_token

    # WHY: BOL Client Credentials = just re-fetch token (no refresh_token needed)
    client_id = conn.raw_data.get("client_id", "") if conn.raw_data else ""
    client_secret = conn.raw_data.get("client_secret", "") if conn.raw_data else ""

    if not client_id or not client_secret:
        logger.error("bol_missing_credentials")
        return None

    result = await validate_bol_credentials(client_id, client_secret)
    if not result["valid"]:
        conn.status = "expired"
        conn.updated_at = now
        db.commit()
        return None

    conn.access_token = result["token"]
    conn.token_expires_at = now + timedelta(seconds=result["expires_in"])
    conn.updated_at = now
    db.commit()

    logger.info("bol_token_refreshed", expires_in=result["expires_in"])
    return conn.access_token


async def fetch_bol_offers(db: Session, user_id: str = "default") -> Dict:
    """Fetch all offers from connected BOL.com seller account.

    WHY paginated: BOL returns max 50 offers/page. We loop through all pages
    to get the full catalog, same pattern as Allegro fetch_seller_offers().
    """
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == "bol",
    ).first()

    if not conn or conn.status != "active":
        return {"store_name": "", "urls": [], "total": 0,
                "error": "BOL.com nie jest połączony. Kliknij 'Połącz' w Integracje.",
                "capped": False}

    token = await _get_fresh_token(conn, db)
    if not token:
        return {"store_name": "", "urls": [], "total": 0,
                "error": "Token BOL.com wygasł. Połącz ponownie.",
                "capped": False}

    all_urls: List[str] = []
    page = 1
    max_pages = 100  # WHY: Guard against infinite loop — 100 pages * 50 = 5K offers

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(max_pages):
                resp = await client.get(
                    f"{BOL_API_BASE}/offers",
                    params={"page": page, "size": 50},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": BOL_ACCEPT,
                    },
                )

                if resp.status_code == 401:
                    return {"store_name": "", "urls": [], "total": 0,
                            "error": "Token BOL.com wygasł. Połącz ponownie.",
                            "capped": False}

                if resp.status_code != 200:
                    return {"store_name": "", "urls": [], "total": 0,
                            "error": f"BOL.com API error: {resp.status_code}",
                            "capped": False}

                data = resp.json()
                offers = data.get("offers", [])

                for offer in offers:
                    offer_id = offer.get("offerId", "")
                    if offer_id:
                        all_urls.append(f"https://www.bol.com/nl/nl/p/-/{offer_id}/")

                # WHY: No more pages when fewer than 50 results
                if len(offers) < 50:
                    break
                page += 1

        logger.info("bol_offers_fetched", total=len(all_urls))
        return {
            "store_name": conn.seller_name or "Twoje konto BOL.com",
            "urls": all_urls,
            "total": len(all_urls),
            "error": None,
            "capped": False,
        }

    except httpx.TimeoutException:
        return {"store_name": "", "urls": [], "total": 0,
                "error": "BOL.com API timeout", "capped": False}
    except Exception as e:
        logger.error("bol_api_error", error=str(e))
        return {"store_name": "", "urls": [], "total": 0,
                "error": f"BOL.com API error: {str(e)}", "capped": False}
