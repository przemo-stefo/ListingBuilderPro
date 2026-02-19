# backend/services/ppc_service.py
# Purpose: PPC campaign recommendations — post-processing, zero LLM calls
# NOT for: Actual PPC campaign management or bid optimization

from __future__ import annotations

from typing import List, Dict, Any
from services.coverage_service import extract_words, keyword_covered
import structlog

logger = structlog.get_logger()


def generate_ppc_recommendations(
    keywords_sorted: List[Dict[str, Any]],
    listing_text: str,
) -> Dict[str, Any]:
    """
    Generate PPC match-type recommendations from keyword research data.
    WHY: DataDive's approach — high-RJ keywords get exact match (lower ACoS),
    mid-range get phrase match, long-tail get broad match.
    Zero LLM cost — pure post-processing of existing keyword data.
    """
    # WHY: Word-set matching — "cap" won't falsely match "capsule"
    listing_words = extract_words(listing_text)
    exact_match: List[Dict[str, Any]] = []
    phrase_match: List[Dict[str, Any]] = []
    broad_match: List[Dict[str, Any]] = []
    negative: List[str] = []

    for i, kw in enumerate(keywords_sorted):
        phrase = kw["phrase"]
        volume = kw.get("search_volume", 0)
        entry = {"phrase": phrase, "search_volume": volume}

        # WHY: Word-boundary check — reuses coverage_service logic for consistency
        is_indexed = keyword_covered(phrase, listing_words)

        if i < 10 and volume >= 1000:
            # WHY: Top 10 high-volume = exact match for maximum conversion at lowest ACoS
            entry["indexed"] = is_indexed
            entry["rationale"] = "Top RJ + high volume — exact match for best ACoS"
            exact_match.append(entry)
        elif i < 30 or volume >= 500:
            # WHY: Mid-range keywords — phrase match captures related searches
            entry["indexed"] = is_indexed
            entry["rationale"] = "Mid-range RJ — phrase match for reach + relevance"
            phrase_match.append(entry)
        elif volume > 0:
            # WHY: Long-tail keywords — broad match discovers new search terms
            entry["indexed"] = is_indexed
            entry["rationale"] = "Long-tail — broad match for discovery"
            broad_match.append(entry)

    # WHY: Flag competitor brand names as negative keywords
    # Simple heuristic: words that look like brand names (capitalized, short)
    # This is a starting point — user should review and adjust
    negative = _detect_competitor_terms(keywords_sorted)

    # WHY: Slice to max display counts, then use sliced lists for summary
    # so counts match the number of items the client actually receives
    exact_out = exact_match[:15]
    phrase_out = phrase_match[:20]
    broad_out = broad_match[:25]
    negative_out = negative[:10]

    logger.debug(
        "ppc_recommendations_generated",
        exact=len(exact_out), phrase=len(phrase_out),
        broad=len(broad_out), negative=len(negative_out),
    )

    return {
        "exact_match": exact_out,
        "phrase_match": phrase_out,
        "broad_match": broad_out,
        "negative_suggestions": negative_out,
        "summary": {
            "exact_count": len(exact_out),
            "phrase_count": len(phrase_out),
            "broad_count": len(broad_out),
            "negative_count": len(negative_out),
            "estimated_daily_budget_usd": _estimate_budget(exact_match, phrase_match),
        },
    }


def _detect_competitor_terms(keywords: List[Dict[str, Any]]) -> List[str]:
    """
    Flag potential competitor brand names in keyword list.
    WHY: Bidding on competitor brands is expensive and low-converting —
    better to add them as negatives unless doing offensive targeting.
    """
    # WHY: Simple heuristic — single words with all lowercase that don't look
    # like generic terms might be brands. This is imperfect but useful as suggestions.
    suspects: List[str] = []
    generic_words = {
        "set", "kit", "pack", "box", "case", "bag", "holder", "stand",
        "cover", "mat", "pad", "tool", "bottle", "cup", "glass", "plate",
        # WHY: Extended list — reviewer flagged false positives on material/shape words
        "ceramic", "bamboo", "silicone", "stainless", "steel", "plastic",
        "wooden", "metal", "rubber", "cotton", "leather", "foam", "nylon",
        "large", "small", "mini", "extra", "heavy", "light", "slim", "flat",
        "round", "square", "long", "short", "wide", "narrow", "thick", "thin",
        "black", "white", "blue", "green", "pink", "grey", "gray", "brown",
        "premium", "professional", "portable", "reusable", "universal",
        "waterproof", "outdoor", "indoor", "travel", "kitchen", "garden",
        "bathroom", "bedroom", "office", "storage", "organizer", "cleaner",
    }
    for kw in keywords:
        words = kw["phrase"].lower().split()
        # WHY: Single-word keywords that aren't generic product terms might be brands.
        # This is a heuristic — users should always review suggestions before applying.
        if len(words) == 1 and words[0] not in generic_words and len(words[0]) >= 4:
            suspects.append(kw["phrase"])
    return suspects


def _estimate_budget(
    exact: List[Dict[str, Any]], phrase: List[Dict[str, Any]],
) -> float:
    """
    Rough daily budget estimate based on keyword volumes.
    WHY: Gives sellers a starting point — $0.50-1.00 CPC * estimated clicks.
    """
    total_volume = sum(k.get("search_volume", 0) for k in exact + phrase)
    # WHY: Assume 1% CTR, $0.75 avg CPC — very rough starting estimate
    estimated_daily_clicks = (total_volume / 30) * 0.01
    return round(estimated_daily_clicks * 0.75, 2)
