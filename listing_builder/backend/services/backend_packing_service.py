# backend/services/backend_packing_service.py
# Purpose: Greedy byte-packing of backend keywords (max 249 bytes for Amazon)
# NOT for: LLM calls, keyword placement, or coverage calculation

from __future__ import annotations

import re
from typing import List, Dict, Any
from services.coverage_service import extract_words as _extract_words


def pack_backend_keywords(
    keywords: List[Dict[str, Any]], listing_text: str, max_bytes: int,
    llm_suggestions: str = "",
) -> str:
    """
    Greedy byte-packing: add keywords not already in the listing text,
    separated by spaces, up to max_bytes (249 for Amazon).
    WHY: Four passes — unused phrases, root words, plural/singular variants,
    then LLM-suggested terms. This maximizes search coverage.
    """
    if max_bytes <= 0:
        return ""

    # WHY: Word-set for consistent matching with coverage_service — "cap" won't match "capsule"
    listing_word_set = _extract_words(listing_text)
    packed: List[str] = []
    packed_words: set = set()
    current_bytes = 0

    def _try_add(text: str) -> bool:
        nonlocal current_bytes
        text_bytes = len(text.encode("utf-8"))
        separator_bytes = 1 if packed else 0
        if current_bytes + separator_bytes + text_bytes <= max_bytes:
            packed.append(text)
            current_bytes += separator_bytes + text_bytes
            packed_words.update(text.lower().split())
            return True
        return False

    # Pass 1: full phrases not already covered in listing
    for kw in keywords:
        phrase = kw["phrase"].strip()
        phrase_words = phrase.lower().split()
        if all(w in listing_word_set for w in phrase_words):
            continue
        _try_add(phrase)

    # Pass 2: individual root words not in listing or already packed
    # WHY: Amazon indexes individual words — adding roots that aren't
    # in visible content expands search match surface within 249 bytes
    all_roots: Dict[str, int] = {}
    for kw in keywords:
        for w in kw["phrase"].lower().split():
            w = w.strip(".,;:-()[]")
            if len(w) >= 2:
                all_roots[w] = all_roots.get(w, 0) + kw.get("search_volume", 0)

    for word, _ in sorted(all_roots.items(), key=lambda x: x[1], reverse=True):
        if word in listing_word_set or word in packed_words:
            continue
        _try_add(word)

    # Pass 3: plural/singular variants to catch alternate searches
    # WHY: Amazon treats "bottle" and "bottles" as different search terms
    # WHY: Adjectives, prepositions, abbreviations don't have useful plural forms
    skip_variant = {
        "bpa", "ml", "cm", "kg", "oz", "mm", "xl", "xxl",
        "free", "steel", "stainless", "insulated", "vacuum",
        "safe", "portable", "durable", "large", "small",
        "cold", "warm", "with", "from", "pour", "pour",
    }
    combined_words = listing_word_set | packed_words
    variants: List[str] = []
    for word in list(all_roots.keys()):
        if len(word) < 4 or word in skip_variant or any(c.isdigit() for c in word):
            continue
        if word.endswith("s") and len(word) > 4 and len(word) <= 9:
            singular = word[:-1]
            if singular not in combined_words and singular not in packed_words:
                variants.append(singular)
        elif not word.endswith("s") and len(word) <= 8:
            plural = word + "s"
            if plural not in combined_words and plural not in packed_words:
                variants.append(plural)
        # German: -e endings → -en plural (Flasche→Flaschen)
        if word.endswith("e") and len(word) >= 8:
            de_plural = word + "n"
            if de_plural not in combined_words and de_plural not in packed_words:
                variants.append(de_plural)

    for v in variants:
        _try_add(v)

    # Pass 4: LLM-suggested synonyms and related terms
    # WHY: When visible coverage is 93%+, Passes 1-3 find almost nothing.
    if llm_suggestions:
        # WHY: LLM output could contain special chars or HTML — strip to alphanumeric words only.
        # Defense in depth: even though our own LLM generates this, a compromised model could
        # inject garbage. Only allow clean word characters through.
        cleaned_suggestions = re.sub(r'[^\w\s]', ' ', llm_suggestions)
        all_known_words = listing_word_set | packed_words
        for term in cleaned_suggestions.lower().split():
            if len(term) < 2 or term in all_known_words or term in packed_words:
                continue
            _try_add(term)

    return " ".join(packed)
