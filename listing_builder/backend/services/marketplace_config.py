# backend/services/marketplace_config.py
# Purpose: Marketplace-specific limits and language detection
# NOT for: Business logic, LLM calls, or compliance checks

from __future__ import annotations


# WHY: Marketplace-specific limits for title, bullets, description, backend keywords
MARKETPLACE_LIMITS = {
    "amazon_de": {"title": 200, "bullet": 500, "backend": 249, "lang": "de"},
    "amazon_com": {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},
    "amazon_us":  {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},
    "amazon_pl":  {"title": 200, "bullet": 500, "backend": 249, "lang": "pl"},
    "amazon_fr":  {"title": 200, "bullet": 500, "backend": 249, "lang": "fr"},
    "amazon_it":  {"title": 200, "bullet": 500, "backend": 249, "lang": "it"},
    "amazon_es":  {"title": 200, "bullet": 500, "backend": 249, "lang": "es"},
    "ebay_de":    {"title": 80,  "bullet": 300, "backend": 0,   "lang": "de"},
    "kaufland":   {"title": 150, "bullet": 400, "backend": 0,   "lang": "de"},
    "allegro":    {"title": 75,  "bullet": 500, "backend": 0,   "lang": "pl"},
}


def get_limits(marketplace: str) -> dict:
    """Return character/byte limits for a given marketplace."""
    return MARKETPLACE_LIMITS.get(marketplace, MARKETPLACE_LIMITS["amazon_de"])


def detect_language(marketplace: str, explicit_lang: str | None) -> str:
    """Resolve language — explicit override wins, else marketplace default."""
    if explicit_lang:
        return explicit_lang
    return get_limits(marketplace).get("lang", "de")
