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


def _empty_result(error: str) -> Dict:
    """WHY extracted: 8 return points used the same dict shape — DRY."""
    return {"store_name": "", "urls": [], "total": 0, "error": error, "capped": False}


async def _start_export(client: httpx.AsyncClient, headers: Dict) -> Dict:
    """Step 1: Request BOL CSV export, return processStatusId or error."""
    resp = await client.post(
        f"{BOL_API_BASE}/offers/export", headers=headers, json={"format": "CSV"},
    )
    if resp.status_code not in (200, 202):
        logger.error("bol_export_start_failed", status=resp.status_code)
        return {"error": f"BOL.com export error: {resp.status_code}"}

    process_id = resp.json().get("processStatusId")
    if not process_id:
        return {"error": "BOL.com nie zwrócił processStatusId"}
    return {"process_id": process_id}


async def _poll_export(client: httpx.AsyncClient, process_id: str, token: str) -> Dict:
    """Step 2: Poll until SUCCESS (max 30s = 10 polls * 3s), return entityId or error."""
    poll_headers = {"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT}
    for _ in range(10):
        await asyncio.sleep(3)
        poll = await client.get(f"{BOL_PROCESS_URL}/{process_id}", headers=poll_headers)
        if poll.status_code != 200:
            continue
        data = poll.json()
        status = data.get("status", "")
        if status == "SUCCESS":
            return {"entity_id": data.get("entityId")}
        if status in ("FAILURE", "TIMEOUT"):
            return {"error": f"BOL.com export failed: {status}"}
    return {"error": "BOL.com export timeout — spróbuj ponownie"}


def _parse_offers_csv(csv_text: str) -> List[str]:
    """Step 3: Parse CSV for offerId/EAN → build BOL.com product URLs.

    WHY EAN first: BOL product URLs use EAN (public page), offerId as search fallback.
    """
    urls: List[str] = []
    for row in csv.DictReader(io.StringIO(csv_text)):
        offer_id = row.get("offerId", "")
        ean = row.get("ean", "")
        if offer_id:
            if ean:
                urls.append(f"https://www.bol.com/nl/nl/p/-/{ean}/")
            else:
                urls.append(f"https://www.bol.com/nl/nl/s/?searchtext={offer_id}")
    return urls


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
        return _empty_result("BOL.com nie jest połączony. Kliknij 'Połącz' w Integracje.")

    token = await _get_fresh_token(conn, db)
    if not token:
        return _empty_result("Token BOL.com wygasł. Połącz ponownie.")

    json_headers = {"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT,
                    "Content-Type": BOL_ACCEPT}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            step1 = await _start_export(client, json_headers)
            if "error" in step1:
                return _empty_result(step1["error"])

            step2 = await _poll_export(client, step1["process_id"], token)
            if "error" in step2:
                return _empty_result(step2["error"])

            csv_resp = await client.get(
                f"{BOL_API_BASE}/offers/export/{step2['entity_id']}",
                headers={"Authorization": f"Bearer {token}", "Accept": BOL_ACCEPT_CSV},
            )
            if csv_resp.status_code != 200:
                logger.error("bol_export_download_failed", status=csv_resp.status_code)
                return _empty_result(f"BOL.com CSV download error: {csv_resp.status_code}")

        all_urls = _parse_offers_csv(csv_resp.text)
        logger.info("bol_offers_fetched", total=len(all_urls))
        return {
            "store_name": conn.seller_name or "Twoje konto BOL.com",
            "urls": all_urls,
            "total": len(all_urls),
            "error": None,
            "capped": False,
        }

    except httpx.TimeoutException:
        return _empty_result("BOL.com API timeout")
    except Exception as e:
        logger.error("bol_api_error", error=str(e))
        return _empty_result(f"BOL.com API error: {str(e)}")
