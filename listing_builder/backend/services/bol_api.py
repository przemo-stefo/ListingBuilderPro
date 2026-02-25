# backend/services/bol_api.py
# Purpose: BOL.com Retailer API v10 client — fetch offers via Client Credentials
# NOT for: OAuth browser redirect flow (BOL uses server-to-server only)

import asyncio
import csv
import io
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
BOL_ACCEPT_CSV = "application/vnd.retailer.v10+csv"
BOL_PROCESS_URL = "https://api.bol.com/shared/process-status"


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

    WHY 3-step async export: BOL v10 API removed GET /offers. New flow is:
    1. POST /offers/export {"format":"CSV"} → processStatusId
    2. Poll /shared/process-status/{id} until SUCCESS → entityId
    3. GET /offers/export/{entityId} with CSV accept → parse offer IDs
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

    json_headers = {"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT,
                    "Content-Type": BOL_ACCEPT}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: Request CSV export
            resp = await client.post(
                f"{BOL_API_BASE}/offers/export",
                headers=json_headers,
                json={"format": "CSV"},
            )
            if resp.status_code not in (200, 202):
                logger.error("bol_export_start_failed", status=resp.status_code, body=resp.text[:300])
                return {"store_name": "", "urls": [], "total": 0,
                        "error": f"BOL.com export error: {resp.status_code}", "capped": False}

            process_id = resp.json().get("processStatusId")
            if not process_id:
                return {"store_name": "", "urls": [], "total": 0,
                        "error": "BOL.com nie zwrócił processStatusId", "capped": False}

            # Step 2: Poll until SUCCESS (max 30s = 10 polls * 3s)
            entity_id = None
            for _ in range(10):
                await asyncio.sleep(3)
                poll = await client.get(
                    f"{BOL_PROCESS_URL}/{process_id}",
                    headers={"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT},
                )
                if poll.status_code != 200:
                    continue
                data = poll.json()
                status = data.get("status", "")
                if status == "SUCCESS":
                    entity_id = data.get("entityId")
                    break
                if status in ("FAILURE", "TIMEOUT"):
                    return {"store_name": "", "urls": [], "total": 0,
                            "error": f"BOL.com export failed: {status}", "capped": False}

            if not entity_id:
                return {"store_name": "", "urls": [], "total": 0,
                        "error": "BOL.com export timeout — spróbuj ponownie", "capped": False}

            # Step 3: Download CSV
            csv_resp = await client.get(
                f"{BOL_API_BASE}/offers/export/{entity_id}",
                headers={"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT_CSV},
            )
            if csv_resp.status_code != 200:
                logger.error("bol_export_download_failed", status=csv_resp.status_code)
                return {"store_name": "", "urls": [], "total": 0,
                        "error": f"BOL.com CSV download error: {csv_resp.status_code}", "capped": False}

        # WHY: Parse CSV for offerId column → build BOL.com product URLs
        all_urls: List[str] = []
        reader = csv.DictReader(io.StringIO(csv_resp.text))
        for row in reader:
            offer_id = row.get("offerId", "")
            ean = row.get("ean", "")
            if offer_id:
                # WHY: BOL product URLs use EAN, not offerId. But offerId is unique per seller.
                # Use EAN-based URL when available (public product page), offerId as fallback.
                if ean:
                    all_urls.append(f"https://www.bol.com/nl/nl/p/-/{ean}/")
                else:
                    all_urls.append(f"https://www.bol.com/nl/nl/s/?searchtext={offer_id}")

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
