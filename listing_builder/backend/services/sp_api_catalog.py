# backend/services/sp_api_catalog.py
# Purpose: Fetch Amazon product data via SP-API Catalog Items v2022-04-01
# NOT for: Token management (sp_api_auth) or report fetching (epr_service)

import httpx
import structlog
from typing import Dict, Optional

from services.sp_api_auth import get_access_token, credentials_configured

logger = structlog.get_logger()

SP_API_BASE = "https://sellingpartnerapi-eu.amazon.com"
CATALOG_API = f"{SP_API_BASE}/catalog/2022-04-01/items"

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


async def fetch_catalog_item(asin: str, marketplace: str = "DE") -> Dict:
    """Fetch product data from SP-API Catalog Items by ASIN.

    WHY SP-API over scraping: Reliable, no anti-bot, structured data,
    returns title, bullet points, images, and product attributes.
    """
    if not credentials_configured():
        return {"error": "Amazon SP-API nie skonfigurowane (brak client_id/secret)"}

    marketplace_id = MARKETPLACE_IDS.get(marketplace.upper(), MARKETPLACE_IDS["DE"])

    try:
        token = await get_access_token()
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

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{CATALOG_API}/{asin}",
                headers=headers,
                params=params,
            )

        if resp.status_code == 404:
            return {"error": f"ASIN {asin} nie znaleziony na Amazon {marketplace}"}

        if resp.status_code == 403:
            return {"error": "Brak dostępu do Catalog API — sprawdź uprawnienia aplikacji SP-API"}

        if resp.status_code != 200:
            logger.warning("sp_api_catalog_error", status=resp.status_code, body=resp.text[:200])
            return {"error": f"SP-API error {resp.status_code}: {resp.text[:100]}"}

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
