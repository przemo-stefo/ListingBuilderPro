# backend/services/keyword_placement_service.py
# Purpose: DataDive keyword placement strategy — assign keywords to title/bullets/backend/description by RJ
# NOT for: Coverage calculation (that's coverage_service.py) or anti-stuffing checks

from __future__ import annotations

from typing import List, Dict, Any, Tuple

# WHY: DataDive's placement strategy assigns keywords by Ranking Juice (search_volume as proxy)
# Title gets the highest-RJ keywords, bullets get mid-range, backend gets long-tail
SELLER_RANGES = {
    "title": (0, 7),        # Top 7 keywords → title
    "bullets": (7, 32),     # Keywords 7-32 → 5 bullet points
    "backend": (32, 100),   # Keywords 32-100 → backend search terms
    "description": (100, 200),  # Remainder → product description
}

VENDOR_RANGES = {
    "title": (0, 7),        # Same top 7 for title
    "bullets": (7, 52),     # Keywords 7-52 → 10 bullet points (Vendor gets more bullets)
    "backend": (52, 120),   # Adjusted backend range
    "description": (120, 250),
}

# WHY: Amazon category-specific bullet character limits — exceeding causes suppression
CATEGORY_BULLET_LIMITS: Dict[str, int] = {
    "apparel": 150,
    "clothing": 150,
    "shoes": 150,
    "jewelry": 150,
    "fashion": 150,
    # Default for all other categories handled in get_bullet_limit()
}
DEFAULT_BULLET_LIMIT = 200


def get_bullet_limit(category: str) -> int:
    """Return max chars per bullet for the given category."""
    if not category:
        return DEFAULT_BULLET_LIMIT
    cat_lower = category.lower()
    for key, limit in CATEGORY_BULLET_LIMITS.items():
        if key in cat_lower:
            return limit
    return DEFAULT_BULLET_LIMIT


def get_bullet_count(account_type: str) -> int:
    """Seller = 5 bullets, Vendor = 10 bullets."""
    return 10 if account_type == "vendor" else 5


def prepare_keywords_by_rj(
    keywords: List[Dict[str, Any]],
    account_type: str = "seller",
) -> Tuple[List[dict], List[dict], List[dict], List[dict], List[dict]]:
    """
    Sort by search_volume desc, assign to placement tiers using DataDive ranges.
    Returns (all_sorted, title_kw, bullets_kw, backend_kw, description_kw).
    """
    sorted_kw = sorted(keywords, key=lambda k: k.get("search_volume", 0), reverse=True)
    ranges = VENDOR_RANGES if account_type == "vendor" else SELLER_RANGES

    title_kw = sorted_kw[ranges["title"][0]:ranges["title"][1]]
    bullets_kw = sorted_kw[ranges["bullets"][0]:ranges["bullets"][1]]
    backend_kw = sorted_kw[ranges["backend"][0]:ranges["backend"][1]]
    description_kw = sorted_kw[ranges["description"][0]:ranges["description"][1]]

    return sorted_kw, title_kw, bullets_kw, backend_kw, description_kw


def prepare_keywords_with_fallback(
    keywords: List[Dict[str, Any]],
    account_type: str = "seller",
) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """
    Wrapper that maps DataDive 5-tier output back to optimizer_service's 4-tier format.
    WHY: Existing optimizer code expects (all, tier1, tier2, tier3) — we merge
    description_kw into tier3 for backward compatibility.
    """
    all_kw, title_kw, bullets_kw, backend_kw, description_kw = prepare_keywords_by_rj(
        keywords, account_type
    )
    # WHY: tier3 = backend + description keywords (both go to lower-priority placements)
    tier3 = backend_kw + description_kw
    return all_kw, title_kw, bullets_kw, tier3
