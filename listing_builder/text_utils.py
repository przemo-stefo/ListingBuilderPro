#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/text_utils.py
# Purpose: Text utility functions for Amazon listing optimization
# NOT for: Business logic or data processing

"""
Text Utilities
Common text processing functions used across modules.
"""

from typing import Set

# WHY: Promotional words forbidden by Amazon
PROMO_WORDS = {'best', 'top', 'sale', 'discount', 'cheap', 'guarantee', 'free', 'warranty'}


def capitalize_title(title: str) -> str:
    """
    Capitalize title following Amazon conventions.

    WHY: Amazon style = First Letter Of Each Major Word
    WHY: Don't capitalize: for, with, and, the, of, to, in, on, a, an
    """
    lowercase_words = {'for', 'with', 'and', 'the', 'of', 'to', 'in', 'on', 'a', 'an'}

    parts = title.split(' - ')
    capitalized_parts = []

    for part in parts:
        words = part.split()
        cap_words = []

        for i, word in enumerate(words):
            # WHY: Always capitalize first word, brand names, and major words
            if i == 0 or word.lower() not in lowercase_words or len(word) <= 2:
                cap_words.append(word.capitalize())
            else:
                cap_words.append(word.lower())

        capitalized_parts.append(' '.join(cap_words))

    return ' - '.join(capitalized_parts)


def contains_promo_words(text: str) -> bool:
    """
    Check if text contains promotional words.

    WHY: Amazon forbids promotional language in listings
    WHY: Used across title, bullets, description
    """
    text_lower = text.lower()
    return any(promo in text_lower for promo in PROMO_WORDS)


def get_promo_words_in_text(text: str) -> Set[str]:
    """
    Get set of promotional words found in text.

    WHY: For detailed validation reporting
    """
    text_lower = text.lower()
    found = set()

    for promo in PROMO_WORDS:
        if promo in text_lower:
            found.add(promo)

    return found


def filter_promo_phrases(phrases: list[str]) -> list[str]:
    """
    Filter out phrases containing promotional words.

    WHY: Clean keyword lists before using in listings
    WHY: Prevents validation errors
    """
    return [p for p in phrases if not contains_promo_words(p)]
