# backend/services/allegro_categories.py
# Purpose: Allegro category search + parameter fetching via REST API
# NOT for: Offer fetching (allegro_api.py) or OAuth flow (oauth_service.py)

import httpx
import structlog
from typing import List, Dict, Optional

from services.allegro_api import get_client_credentials_token, ALLEGRO_API_BASE, _client_token_cache

logger = structlog.get_logger()

# WHY: In-memory cache — category structure rarely changes, avoids repeat API calls
# WHY: Max 500 entries — prevents OOM from unbounded growth on long-running instances
_MAX_CACHE_SIZE = 500
_category_cache: Dict[str, List[dict]] = {}
_params_cache: Dict[str, List[dict]] = {}
_category_by_id_cache: Dict[str, dict] = {}


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


async def fetch_category_by_id(category_id: str) -> Optional[dict]:
    """Fetch a single Allegro category by ID and build full path via parent chain.

    WHY: When resolving an Allegro URL, we get category_id from the offer
    but need the full name + path for the attribute generation form.
    """
    if category_id in _category_by_id_cache:
        return _category_by_id_cache[category_id]

    token = await get_client_credentials_token()
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.allegro.public.v1+json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{ALLEGRO_API_BASE}/sale/categories/{category_id}",
                headers=headers,
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            name = data.get("name", "")
            leaf = data.get("leaf", False)

            # WHY: Walk parent chain to build full path (e.g. "Elektronika > Telefony > Smartfony")
            path_parts = [name]
            parent = data.get("parent", {})
            while parent and parent.get("id"):
                parent_resp = await client.get(
                    f"{ALLEGRO_API_BASE}/sale/categories/{parent['id']}",
                    headers=headers,
                )
                if parent_resp.status_code != 200:
                    break
                parent_data = parent_resp.json()
                path_parts.insert(0, parent_data.get("name", ""))
                parent = parent_data.get("parent", {})

            result = {
                "id": str(category_id),
                "name": name,
                "path": " > ".join(path_parts),
                "leaf": leaf,
            }

            if len(_category_by_id_cache) >= _MAX_CACHE_SIZE:
                _category_by_id_cache.clear()
            _category_by_id_cache[category_id] = result
            return result

    except Exception as e:
        logger.error("allegro_category_by_id_error", error=str(e), category_id=category_id)
        return None


async def fetch_category_parameters(category_id: str) -> List[dict]:
    """Fetch all parameters for an Allegro category.

    Uses GET /sale/categories/{categoryId}/parameters.
    Returns list of params with type, required flag, options (for DICTIONARY), restrictions.
    WHY retry: Transient token failures (expired/revoked) caused "Nie znaleziono parametrów"
    errors — one retry with token invalidation fixes it transparently.
    """
    if category_id in _params_cache:
        return _params_cache[category_id]

    # WHY: 2 attempts — if first fails due to stale token, invalidate and retry once
    resp = None
    for attempt in range(2):
        token = await get_client_credentials_token()
        if not token:
            logger.error("allegro_params_no_token", attempt=attempt)
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
        except Exception as e:
            logger.error("allegro_params_request_error", error=str(e), attempt=attempt)
            if attempt == 0:
                _client_token_cache["token"] = None
                continue
            return []

        if resp.status_code == 200:
            break

        # WHY: 401/403 = stale token — invalidate cache and retry
        if resp.status_code in (401, 403) and attempt == 0:
            logger.warning("allegro_params_auth_retry", status=resp.status_code, category_id=category_id)
            _client_token_cache["token"] = None
            continue

        logger.error("allegro_params_fetch_failed", status=resp.status_code, category_id=category_id)
        return []

    if not resp or resp.status_code != 200:
        return []

    try:
        data = resp.json()
        params = []
        for p in data.get("parameters", []):
            param = {
                "id": str(p["id"]),
                "name": p.get("name", ""),
                "type": p.get("type", "STRING"),
                "required": p.get("required", False),
                # WHY: Allegro returns unit as dict {"name": "kg"} OR plain str "kg" depending on category
                "unit": p["unit"].get("name") if isinstance(p.get("unit"), dict) else p.get("unit"),
                "options": [],
                "restrictions": p.get("restrictions", {}),
            }
            # WHY: DICTIONARY params have predefined values — LLM must pick from these
            if p.get("type") == "dictionary" or p.get("dictionary"):
                raw_dict = p.get("dictionary", {})
                # WHY: Allegro returns dictionary as list [...] OR dict {"values": [...]} depending on category
                values = raw_dict if isinstance(raw_dict, list) else raw_dict.get("values", [])
                for item in values:
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
        logger.error("allegro_params_parse_error", error=str(e), category_id=category_id)
        return []
