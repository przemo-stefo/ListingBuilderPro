# backend/services/allegro_categories.py
# Purpose: Allegro category search + parameter fetching via REST API
# NOT for: Offer fetching (allegro_api.py) or OAuth flow (oauth_service.py)

import httpx
import structlog
from typing import List, Dict, Optional

from services.allegro_api import get_client_credentials_token, ALLEGRO_API_BASE

logger = structlog.get_logger()

# WHY: In-memory cache — category structure rarely changes, avoids repeat API calls
# WHY: Max 500 entries — prevents OOM from unbounded growth on long-running instances
_MAX_CACHE_SIZE = 500
_category_cache: Dict[str, List[dict]] = {}
_params_cache: Dict[str, List[dict]] = {}


async def search_categories(query: str) -> List[dict]:
    """Search Allegro categories matching a product query.

    Uses GET /sale/matching-categories — returns top matches with paths.
    Results are cached in-memory by query string.
    """
    cache_key = query.strip().lower()
    if cache_key in _category_cache:
        return _category_cache[cache_key]

    token = await get_client_credentials_token()
    if not token:
        logger.error("allegro_categories_no_token")
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/sale/matching-categories",
                params={"name": query},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.allegro.public.v1+json",
                },
            )

        if resp.status_code != 200:
            logger.error("allegro_category_search_failed", status=resp.status_code, query=query)
            return []

        data = resp.json()
        categories = []
        for cat in data.get("matchingCategories", []):
            path_parts = [p.get("name", "") for p in cat.get("path", [])]
            categories.append({
                "id": str(cat["id"]),
                "name": cat.get("name", ""),
                "path": " > ".join(path_parts) if path_parts else cat.get("name", ""),
                "leaf": cat.get("leaf", False),
            })

        if len(_category_cache) >= _MAX_CACHE_SIZE:
            _category_cache.clear()
        _category_cache[cache_key] = categories
        logger.info("allegro_categories_found", query=query, count=len(categories))
        return categories

    except Exception as e:
        logger.error("allegro_category_search_error", error=str(e), query=query)
        return []


async def fetch_category_parameters(category_id: str) -> List[dict]:
    """Fetch all parameters for an Allegro category.

    Uses GET /sale/categories/{categoryId}/parameters.
    Returns list of params with type, required flag, options (for DICTIONARY), restrictions.
    """
    if category_id in _params_cache:
        return _params_cache[category_id]

    token = await get_client_credentials_token()
    if not token:
        logger.error("allegro_params_no_token")
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/sale/categories/{category_id}/parameters",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.allegro.public.v1+json",
                },
            )

        if resp.status_code != 200:
            logger.error("allegro_params_fetch_failed", status=resp.status_code, category_id=category_id)
            return []

        data = resp.json()
        params = []
        for p in data.get("parameters", []):
            param = {
                "id": str(p["id"]),
                "name": p.get("name", ""),
                "type": p.get("type", "STRING"),
                "required": p.get("required", False),
                "unit": p.get("unit", {}).get("name") if p.get("unit") else None,
                "options": [],
                "restrictions": p.get("restrictions", {}),
            }
            # WHY: DICTIONARY params have predefined values — LLM must pick from these
            if p.get("type") == "dictionary" or p.get("dictionary"):
                dictionary = p.get("dictionary", {})
                for item in dictionary.get("values", []):
                    param["options"].append({
                        "id": str(item.get("id", "")),
                        "value": item.get("value", ""),
                    })
                param["type"] = "DICTIONARY"
            else:
                param["type"] = p.get("type", "string").upper()

            params.append(param)

        if len(_params_cache) >= _MAX_CACHE_SIZE:
            _params_cache.clear()
        _params_cache[category_id] = params
        logger.info("allegro_params_fetched", category_id=category_id, count=len(params))
        return params

    except Exception as e:
        logger.error("allegro_params_error", error=str(e), category_id=category_id)
        return []
