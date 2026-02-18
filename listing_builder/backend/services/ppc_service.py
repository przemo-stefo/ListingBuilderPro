# backend/services/ppc_service.py
# Purpose: PPC campaign recommendations — post-processing, zero LLM calls
# NOT for: Actual PPC campaign management or bid optimization

from __future__ import annotations

from typing import List, Dict, Any


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
    listing_lower = listing_text.lower()
    exact_match: List[Dict[str, Any]] = []
    phrase_match: List[Dict[str, Any]] = []
    broad_match: List[Dict[str, Any]] = []
    negative: List[str] = []

    for i, kw in enumerate(keywords_sorted):
        phrase = kw["phrase"]
        volume = kw.get("search_volume", 0)
        entry = {"phrase": phrase, "search_volume": volume}

        # WHY: Check if keyword is actually in the listing (indexed = better relevance score)
        is_indexed = phrase.lower() in listing_lower

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

    return {
        "exact_match": exact_match[:15],
        "phrase_match": phrase_match[:20],
        "broad_match": broad_match[:25],
        "negative_suggestions": negative[:10],
        "summary": {
            "exact_count": len(exact_match),
            "phrase_count": len(phrase_match),
            "broad_count": len(broad_match),
            "negative_count": len(negative),
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
    }
    for kw in keywords:
        words = kw["phrase"].lower().split()
        # Single-word keywords that aren't generic product terms might be brands
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
