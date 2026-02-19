# backend/services/allegro_api.py
# Purpose: Allegro REST API client — fetch offers + product details via OAuth or Client Credentials
# NOT for: OAuth flow (that's oauth_service.py) or HTML scraping (allegro_scraper.py)

import asyncio
import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from config import settings
from models.oauth_connection import OAuthConnection

logger = structlog.get_logger()

ALLEGRO_API_BASE = "https://api.allegro.pl"
ALLEGRO_TOKEN_URL = "https://allegro.pl/auth/oauth/token"

# WHY module-level cache: Client Credentials token is app-level (not per-user),
# so one token serves all requests. Avoids hitting Allegro token endpoint every call.
_client_token_cache: Dict = {"token": None, "expires_at": None}


def _parse_images(data: Dict) -> List[str]:
    """Extract image URLs from offer data — handles both str and dict formats."""
    images = []
    for img in data.get("images", []):
        if isinstance(img, str):
            if img:
                images.append(img)
        elif isinstance(img, dict):
            url = img.get("url", "")
            if url:
                images.append(url)
    return images


def _parse_parameters(param_list: list) -> Dict[str, str]:
    """Parse Allegro parameter list into {name: value} dict."""
    parameters = {}
    for param in param_list:
        name = param.get("name", "")
        values = param.get("values", [])
        if name and values:
            if isinstance(values[0], dict):
                val = ", ".join(v.get("value", "") for v in values if v.get("value"))
            else:
                val = ", ".join(str(v) for v in values if v)
            if val:
                parameters[name] = val
    return parameters


def _parse_description(data: Dict) -> str:
    """Extract text content from Allegro description sections."""
    desc_section = data.get("description", {})
    if not desc_section or not desc_section.get("sections"):
        return ""
    parts = []
    for section in desc_section["sections"]:
        for item in section.get("items", []):
            if item.get("type") == "TEXT":
                parts.append(item.get("content", ""))
    return "\n".join(parts)


def _extract_ean(parameters: Dict[str, str], data: Dict = None) -> str:
    """Extract EAN from parameters, with optional fallback to external.id."""
    for key in ("EAN", "EAN (GTIN)", "GTIN"):
        if key in parameters:
            return parameters[key]
    # WHY: /sale/product-offers sometimes has EAN in external.id instead of parameters
    if data:
        external = data.get("external", {})
        if external.get("id"):
            return external["id"]
    return ""


def _build_offer_result(offer_id: str, data: Dict, parameters: Dict[str, str],
                        ean: str, images: List[str], description: str) -> Dict:
    """Build standardized offer result dict compatible with converter pipeline."""
    title = data.get("name", "")
    price = ""
    currency = "PLN"
    selling_mode = data.get("sellingMode", {})
    if selling_mode.get("price"):
        price = str(selling_mode["price"].get("amount", ""))
        currency = selling_mode["price"].get("currency", "PLN")

    return {
        "source_url": f"https://allegro.pl/oferta/{offer_id}",
        "source_id": offer_id,
        "title": title,
        "description": description,
        "price": price,
        "currency": currency,
        "ean": ean,
        "images": images,
        "category": data.get("category", {}).get("id", ""),
        "quantity": str(data.get("stock", {}).get("available", "1")),
        "condition": data.get("condition", ""),
        "parameters": parameters,
        "brand": parameters.get("Marka", ""),
        "manufacturer": parameters.get("Producent", ""),
        "error": None,
    }


async def get_client_credentials_token() -> Optional[str]:
    """Get app-level Allegro token via Client Credentials grant.

    WHY Client Credentials: No user login needed. Works for public endpoints
    like GET /offers/{offerId}. Token auto-renews from client_id + client_secret.
    Mateusz never gets "logged out" because no user session is involved.
    """
    if not settings.allegro_client_id or not settings.allegro_client_secret:
        return None

    # WHY cache check: Allegro tokens last ~12h, no need to fetch every request
    now = datetime.now(timezone.utc)
    if (_client_token_cache["token"]
            and _client_token_cache["expires_at"]
            and _client_token_cache["expires_at"] > now + timedelta(minutes=5)):
        return _client_token_cache["token"]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                ALLEGRO_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(settings.allegro_client_id, settings.allegro_client_secret),
            )

        if resp.status_code != 200:
            logger.error("allegro_client_token_failed", status=resp.status_code)
            return None

        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 43200)

        _client_token_cache["token"] = token
        _client_token_cache["expires_at"] = now + timedelta(seconds=expires_in)

        logger.info("allegro_client_token_obtained", expires_in=expires_in)
        return token

    except Exception as e:
        logger.error("allegro_client_token_error", error=str(e))
        return None


async def fetch_public_offer_details(offer_id: str) -> Dict:
    """Fetch offer details using public API (no seller login needed).

    WHY public endpoint: Uses GET /offers/{offerId} which works with
    Client Credentials token. No user OAuth required — app token is enough.
    """
    token = await get_client_credentials_token()
    if not token:
        return {"error": "Brak kluczy Allegro API (client_id/client_secret)"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.allegro.public.v1+json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/offers/{offer_id}",
                headers=headers,
            )

            if resp.status_code != 200:
                logger.error("allegro_public_offer_failed",
                             offer_id=offer_id, status=resp.status_code)
                return {"error": f"Allegro API {resp.status_code}"}

            data = resp.json()
            images = _parse_images(data)
            parameters = _parse_parameters(data.get("parameters", []))
            ean = _extract_ean(parameters)
            description = _parse_description(data)
            result = _build_offer_result(offer_id, data, parameters, ean, images, description)

            logger.info("allegro_public_offer_fetched", offer_id=offer_id,
                        title=result["title"][:60], price=result["price"],
                        params=len(parameters))
            return result

    except httpx.TimeoutException:
        return {"error": f"Allegro API timeout for offer {offer_id}"}
    except Exception as e:
        logger.error("allegro_public_offer_error", offer_id=offer_id, error=str(e))
        return {"error": f"Allegro API error: {str(e)}"}


RETRYABLE_STATUSES = {429, 500, 502, 503}
REFRESH_MAX_RETRIES = 3
REFRESH_BACKOFF_BASE = 1  # seconds: 1, 3, 9


async def _refresh_token_if_needed(conn: OAuthConnection, db: Session) -> bool:
    """Refresh Allegro access token if expired, with retry on transient errors.

    WHY retry: Single network blip (429, timeout) used to mark connection "expired",
    forcing Mateusz to re-authorize. 3 retries with exponential backoff fixes this.
    """
    if conn.token_expires_at and conn.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        return True

    if not conn.refresh_token:
        logger.warning("allegro_no_refresh_token")
        return False

    last_error = None
    for attempt in range(REFRESH_MAX_RETRIES):
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

            if resp.status_code == 200:
                data = resp.json()
                conn.access_token = data["access_token"]
                conn.refresh_token = data.get("refresh_token", conn.refresh_token)
                conn.token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=data.get("expires_in", 43200)
                )
                conn.updated_at = datetime.now(timezone.utc)
                db.commit()

                if attempt > 0:
                    logger.info("allegro_token_refreshed", retries=attempt)
                else:
                    logger.info("allegro_token_refreshed")
                return True

            # WHY: 400/401 = invalid refresh token (real expiry) — no point retrying
            if resp.status_code not in RETRYABLE_STATUSES:
                logger.error("allegro_token_refresh_failed",
                             status=resp.status_code, body=resp.text[:200], attempt=attempt + 1)
                break

            # WHY: Retryable status — wait and try again
            last_error = f"HTTP {resp.status_code}"
            logger.warning("allegro_token_refresh_retrying",
                           status=resp.status_code, attempt=attempt + 1)

        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            last_error = str(e)
            logger.warning("allegro_token_refresh_retrying",
                           error=str(e), attempt=attempt + 1)

        except Exception as e:
            logger.error("allegro_token_refresh_error", error=str(e))
            break

        # WHY: Exponential backoff — 1s, 3s, 9s
        if attempt < REFRESH_MAX_RETRIES - 1:
            await asyncio.sleep(REFRESH_BACKOFF_BASE * (3 ** attempt))

    # All retries exhausted or non-retryable error
    logger.error("allegro_token_refresh_exhausted", last_error=last_error)
    conn.status = "expired"
    conn.updated_at = datetime.now(timezone.utc)
    db.commit()
    return False


async def fetch_seller_offers(db: Session, user_id: str = "default") -> Dict:
    """Fetch all active offers from connected Allegro seller account.

    WHY API not scraping: Official API is free, fast (<1s vs 5s/product),
    structured JSON (no HTML parsing), and never blocked by DataDome.

    Returns same format as scrape_allegro_store_urls() for compatibility
    with existing converter pipeline.
    """
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
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
    # WHY: Guard against infinite loop — 100 pages × 1000 = 100K offers max
    max_pages = 100

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for _page in range(max_pages):
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


async def fetch_offer_details(
    offer_id: str, access_token: str
) -> Dict:
    """Fetch full product details from Allegro REST API.

    WHY API not scraping: Structured JSON, no DataDome blocks, no Scrape.do costs.
    Uses GET /sale/product-offers/{offerId} for seller's own offers.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # WHY /sale/product-offers: new endpoint (replaces deprecated /sale/offers/{id})
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/sale/product-offers/{offer_id}",
                headers=headers,
            )

            if resp.status_code != 200:
                logger.error("allegro_offer_detail_failed",
                             offer_id=offer_id, status=resp.status_code)
                return {"error": f"Allegro API {resp.status_code}"}

            data = resp.json()
            images = _parse_images(data)

            # WHY productSet: /sale/product-offers nests params under productSet
            parameters = {}
            product_set = data.get("productSet", [])
            if product_set:
                parameters = _parse_parameters(
                    product_set[0].get("product", {}).get("parameters", [])
                )
            # Also check top-level parameters (some offers have both)
            top_params = _parse_parameters(data.get("parameters", []))
            for name, val in top_params.items():
                if name not in parameters:
                    parameters[name] = val

            ean = _extract_ean(parameters, data)
            description = _parse_description(data)
            result = _build_offer_result(offer_id, data, parameters, ean, images, description)

            logger.info("allegro_offer_fetched", offer_id=offer_id,
                        title=result["title"][:60], price=result["price"],
                        params=len(parameters), images=len(images), has_ean=bool(ean))
            return result

    except httpx.TimeoutException:
        return {"error": f"Allegro API timeout for offer {offer_id}"}
    except Exception as e:
        logger.error("allegro_offer_error", offer_id=offer_id, error=str(e))
        return {"error": f"Allegro API error: {str(e)}"}


async def get_access_token(db: Session, user_id: str = "default") -> Optional[str]:
    """Get valid Allegro access token (refresh if needed).

    WHY separate function: converter_service needs the token directly
    without importing OAuthConnection model.
    """
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == "allegro",
    ).first()

    if not conn or conn.status != "active":
        return None

    if not await _refresh_token_if_needed(conn, db):
        return None

    return conn.access_token
