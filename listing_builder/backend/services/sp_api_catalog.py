# backend/services/sp_api_catalog.py
# Purpose: Fetch Amazon product data via SP-API Catalog Items v2022-04-01
# NOT for: Token management (sp_api_auth) or report fetching (epr_service)

import asyncio
import httpx
import structlog
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from config import settings
from services.sp_api_auth import get_access_token, credentials_configured

logger = structlog.get_logger()

# WHY two bases: Sandbox app uses sandbox endpoint, production app uses production endpoint
SP_API_BASE_PROD = "https://sellingpartnerapi-eu.amazon.com"
SP_API_BASE_SANDBOX = "https://sandbox.sellingpartnerapi-eu.amazon.com"

# WHY: Map marketplace code → Amazon marketplace ID for SP-API
MARKETPLACE_IDS = {
    "DE": "A1PA6795UKMFR9",
    "FR": "A13V1IB3VIYZZH",
    "IT": "APJ6JRA9NG5V4",
    "ES": "A1RKKUPIHCS9HS",
    "PL": "A1C3SOZRARQ6R3",
    "NL": "A1805IZSGTT6HS",
    "SE": "A2NODRKZP88ZB9",
    "UK": "A1F83G8C2ARO7P",
    "US": "ATVPDKIKX0DER",
    "BE": "AMEN7PMS3EDWL",
}


async def fetch_catalog_item(asin: str, marketplace: str = "DE", db: Optional[Session] = None) -> Dict:
    """Fetch product data from SP-API Catalog Items by ASIN.

    WHY SP-API over scraping: Reliable, no anti-bot, structured data,
    returns title, bullet points, images, and product attributes.
    WHY db param: Check oauth_connections for token if not in env.
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane (brak client_id/secret)"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db)
    except (ValueError, RuntimeError) as e:
        return {"error": f"Błąd autoryzacji SP-API: {str(e)[:100]}"}

    headers = {
        "x-amz-access-token": token,
        "Content-Type": "application/json",
    }

    # WHY includedData: summaries has title+brand, attributes has bullets+description,
    # images has product images — all we need for audit
    params = {
        "marketplaceIds": marketplace_id,
        "includedData": "summaries,attributes,images",
    }

    # WHY: Sandbox apps must call sandbox endpoint; production apps call production
    base = SP_API_BASE_SANDBOX if settings.amazon_sandbox else SP_API_BASE_PROD
    catalog_url = f"{base}/catalog/2022-04-01/items/{asin}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                catalog_url,
                headers=headers,
                params=params,
            )

        if resp.status_code == 404:
            return {"error": f"ASIN {asin} nie znaleziony na Amazon {marketplace}"}

        if resp.status_code == 403:
            return {"error": "Brak dostępu do Catalog API — sprawdź uprawnienia aplikacji SP-API"}

        if resp.status_code != 200:
            logger.warning("sp_api_catalog_error", status=resp.status_code)
            return {"error": f"Błąd Amazon SP-API (kod {resp.status_code})"}

        data = resp.json()
        return _parse_catalog_response(data, asin, marketplace)

    except httpx.TimeoutException:
        return {"error": "Amazon SP-API timeout — spróbuj ponownie"}
    except Exception as e:
        logger.error("sp_api_catalog_error", asin=asin, error=str(e))
        return {"error": f"Błąd SP-API: {str(e)[:100]}"}


def _parse_catalog_response(data: Dict, asin: str, marketplace: str) -> Dict:
    """Extract audit-relevant fields from SP-API Catalog Items response.

    WHY separate function: SP-API response is deeply nested —
    isolate parsing logic from network/auth logic.
    """
    result = {
        "asin": asin,
        "marketplace": marketplace,
        "title": "",
        "bullets": [],
        "description": "",
        "brand": "",
        "images": [],
        "manufacturer": "",
        "error": None,
    }

    # Summaries → title, brand, manufacturer
    summaries = data.get("summaries", [])
    if summaries:
        s = summaries[0]
        result["title"] = s.get("itemName", "")
        result["brand"] = s.get("brand", "")
        result["manufacturer"] = s.get("manufacturer", "")

    # Attributes → bullet_point, product_description
    attributes = data.get("attributes", {})

    bullet_points = attributes.get("bullet_point", [])
    for bp in bullet_points:
        val = bp.get("value", "")
        if val:
            result["bullets"].append(val)

    desc_list = attributes.get("product_description", [])
    if desc_list:
        result["description"] = desc_list[0].get("value", "")

    # Images → primary images
    images_data = data.get("images", [])
    for img_set in images_data:
        for img in img_set.get("images", []):
            if img.get("variant", "") == "MAIN" or len(result["images"]) < 7:
                url = img.get("link", "")
                if url and url not in result["images"]:
                    result["images"].append(url)

    logger.info("sp_api_catalog_ok", asin=asin, marketplace=marketplace,
                title_len=len(result["title"]), bullets=len(result["bullets"]),
                images=len(result["images"]))

    return result


async def fetch_catalog_items_batch(
    asins: List[str], marketplace: str = "DE", db: Optional[Session] = None
) -> Dict[str, Dict]:
    """Fetch multiple ASINs in one SP-API call (max 20 per request).

    WHY batch: Single item fetch per product = N API calls.
    SP-API searchCatalogItems supports up to 20 identifiers per request.
    Returns: {asin: parsed_result, ...}
    """
    if not credentials_configured() or not asins:
        return {}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token(db=db)
    except (ValueError, RuntimeError) as e:
        logger.error("sp_api_batch_auth_error", error=str(e)[:100])
        return {}

    base = SP_API_BASE_SANDBOX if settings.amazon_sandbox else SP_API_BASE_PROD
    results: Dict[str, Dict] = {}

    # WHY chunks of 20: SP-API limit for searchCatalogItems identifiers
    for i in range(0, len(asins), 20):
        chunk = asins[i:i + 20]
        if i > 0:
            await asyncio.sleep(0.5)  # WHY: Rate limit protection

        try:
            headers = {
                "x-amz-access-token": token,
                "Content-Type": "application/json",
            }
            params = {
                "identifiers": ",".join(chunk),
                "identifiersType": "ASIN",
                "marketplaceIds": marketplace_id,
                "includedData": "summaries,attributes,images",
            }

            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{base}/catalog/2022-04-01/items",
                    headers=headers,
                    params=params,
                )

            if resp.status_code != 200:
                logger.warning("sp_api_batch_error", status=resp.status_code, chunk_size=len(chunk))
                continue

            data = resp.json()
            for item in data.get("items", []):
                asin = item.get("asin", "")
                if asin:
                    results[asin] = _parse_catalog_response(item, asin, marketplace)

        except Exception as e:
            logger.error("sp_api_batch_chunk_error", error=str(e)[:100], chunk_size=len(chunk))

    logger.info("sp_api_batch_done", requested=len(asins), fetched=len(results))
    return results
