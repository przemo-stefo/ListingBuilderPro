#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/title_builder.py
# Purpose: Build optimized Amazon titles with EXACT phrase matching
# NOT for: Generic text generation or title creation outside Amazon context

"""
Title Builder
Creates Amazon-optimized titles with 7-9 EXACT phrases, 190+ characters.
Uses dash-separated format for maximum EXACT matching.
"""

from typing import List, Dict, Tuple
from text_utils import capitalize_title, PROMO_WORDS


def build_aggressive_title(
    brand: str,
    product_line: str,
    keywords: List[Dict],
    target_length: int = 195,
    exact_phrases_target: int = 8
) -> Tuple[str, Dict]:
    """
    Build aggressive title with 7-9 EXACT phrases, 190+ chars.

    WHY: From transcripts - aggressive mode = 7-9 EXACT phrases
    WHY: Dash-separated format prevents "with"/"for" breaking EXACT matches
    WHY: 190-197 chars = 95%+ utilization of 200 char limit
    WHY: Each dash-separated phrase = potential EXACT match

    Returns: (title_string, stats_dict)
    """
    # WHY: Start with brand + product line (required for brand registry)
    title_parts = [brand]

    if product_line and product_line.lower() not in brand.lower():
        title_parts.append(product_line)

    # WHY: Extract top EXACT phrases (2-4 words work best)
    exact_phrases = _get_top_exact_phrases(keywords, exact_phrases_target * 3)

    # WHY: Add phrases until we reach target length or phrase count
    added_phrases = []
    current_length = len(' - '.join(title_parts))

    for phrase in exact_phrases:
        # WHY: Calculate length if we add this phrase
        test_length = current_length + len(' - ' + phrase)

        # WHY: Stop if we exceed target length (allow small overage)
        if test_length > target_length + 5:
            continue

        added_phrases.append(phrase)
        current_length = test_length

        # WHY: Stop if we hit target EXACT phrase count
        if len(added_phrases) >= exact_phrases_target:
            break

    # WHY: Combine all parts with dash separator (EXACT match friendly)
    all_parts = title_parts + added_phrases
    title = ' - '.join(all_parts)

    # WHY: Capitalize first letter of each major word (Amazon style)
    title = capitalize_title(title)

    stats = {
        'length': len(title),
        'utilization': (len(title) / 200) * 100,
        'exact_phrases': len(added_phrases),
        'brand_included': True
    }

    return title, stats


def build_standard_title(
    brand: str,
    product_line: str,
    keywords: List[Dict],
    target_length: int = 150
) -> Tuple[str, Dict]:
    """
    Build standard title with 3-4 EXACT phrases, 140-150 chars.

    WHY: Standard mode for products with less competitive niches
    WHY: More readable, less aggressive optimization
    """
    title_parts = [brand]

    if product_line:
        title_parts.append(product_line)

    # WHY: Standard mode uses fewer EXACT phrases (3-4 vs 7-9)
    exact_phrases = _get_top_exact_phrases(keywords, 6)

    added_phrases = []
    current_length = len(' - '.join(title_parts))

    for phrase in exact_phrases[:4]:  # WHY: Max 4 phrases for standard
        if _is_phrase_covered(phrase, added_phrases):
            continue

        test_length = current_length + len(' - ' + phrase)

        if test_length > target_length:
            break

        added_phrases.append(phrase)
        current_length = test_length

    all_parts = title_parts + added_phrases
    title = ' - '.join(all_parts)
    title = capitalize_title(title)

    stats = {
        'length': len(title),
        'utilization': (len(title) / 200) * 100,
        'exact_phrases': len(added_phrases),
        'brand_included': True
    }

    return title, stats


def _get_top_exact_phrases(keywords: List[Dict], limit: int) -> List[str]:
    """
    Get top phrases optimized for EXACT matching.

    WHY: 2-4 word phrases work best for title EXACT matches
    WHY: Too short (1 word) = too broad, too long (5+) = too specific
    """
    # WHY: Filter to 2-4 word phrases, no promo words
    good_phrases = []
    for k in keywords:
        phrase = k['phrase']
        if 2 <= k['word_count'] <= 4 and k['relevancy'] >= 0.35:
            # WHY: Skip if contains promotional words
            if not any(promo in phrase.split() for promo in PROMO_WORDS):
                good_phrases.append(phrase)

    return good_phrases[:limit]


def _is_phrase_covered(phrase: str, existing_phrases: List[str]) -> bool:
    """
    Check if phrase is already covered by existing phrases.

    WHY: Avoid redundancy - if "cutting board" exists, skip "wood cutting board"
    WHY: Maximize unique keyword coverage
    """
    phrase_words = set(phrase.split())

    for existing in existing_phrases:
        existing_words = set(existing.split())

        # WHY: If 80%+ of words overlap, consider it covered
        overlap = len(phrase_words & existing_words) / len(phrase_words)
        if overlap >= 0.8:
            return True

    return False
