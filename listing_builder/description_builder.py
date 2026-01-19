#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/description_builder.py
# Purpose: Generate optimized product descriptions with keyword coverage
# NOT for: A+ content, brand story, or other enhanced content

"""
Description Builder
Creates keyword-optimized product descriptions (2000 chars).
"""

from typing import List, Dict
from text_utils import filter_promo_phrases


def generate_description(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    brand: str,
    product_line: str,
    char_limit: int = 2000
) -> str:
    """
    Generate product description with keyword coverage.

    WHY: Description = 2000 char limit on Amazon
    WHY: Less important than title/bullets but still indexed
    WHY: Use tier 3 keywords (0.2-0.3 relevancy) here
    WHY: More natural, storytelling approach vs bullets
    """
    # WHY: Extract tier 3 keywords not yet used in title/bullets
    listing_text = title.lower() + ' '.join(bullets).lower()

    tier3_keywords = [
        k for k in keywords
        if 0.2 <= k['relevancy'] < 0.3 and k['phrase'] not in listing_text
    ]

    # WHY: Filter promotional words from all keywords used in description
    top_10_phrases = [k['phrase'] for k in keywords[:10]]
    top_10_phrases = filter_promo_phrases(top_10_phrases)
    filtered_top_10 = [k for k in keywords[:10] if k['phrase'] in top_10_phrases]

    tier3_phrases = [k['phrase'] for k in tier3_keywords]
    tier3_phrases = filter_promo_phrases(tier3_phrases)
    filtered_tier3 = [k for k in tier3_keywords if k['phrase'] in tier3_phrases]

    # WHY: Build description in 3 paragraphs
    intro = _build_intro_paragraph(brand, product_line, filtered_top_10)
    features = _build_features_paragraph(filtered_tier3[:15])
    closing = _build_closing_paragraph(brand, filtered_tier3[15:25])

    description = f"{intro}\n\n{features}\n\n{closing}"

    # WHY: Truncate if over limit
    if len(description) > char_limit:
        description = description[:char_limit-3] + "..."

    return description


def _build_intro_paragraph(brand: str, product_line: str, keywords: List[Dict]) -> str:
    """
    Build introduction paragraph.

    WHY: Hook buyer with brand story + top keywords
    WHY: Natural language, not keyword stuffing
    """
    top_phrases = [k['phrase'] for k in keywords[:5]]

    intro = f"Welcome to {brand}, where quality meets functionality. "
    intro += f"Our {product_line} is expertly crafted as the perfect {top_phrases[0] if top_phrases else 'solution'} "

    if len(top_phrases) > 1:
        intro += f"for {top_phrases[1]}. "

    intro += f"Whether you're looking for {', '.join(top_phrases[2:4]) if len(top_phrases) > 2 else 'premium quality'}, "
    intro += f"this product delivers exceptional performance and durability."

    return intro


def _build_features_paragraph(keywords: List[Dict]) -> str:
    """
    Build features paragraph with keyword integration.

    WHY: Middle paragraph = feature details
    WHY: Integrate tier 3 keywords naturally
    """
    phrases = [k['phrase'] for k in keywords[:10] if keywords]

    # WHY: Start with generic features text if no keywords
    if not phrases:
        return "Key Features: Premium construction ensures long-lasting durability and exceptional performance for all your needs."

    features = "Key Features: "

    # WHY: List features in natural sentence structure
    if len(phrases) >= 1:
        features += f"Designed for {phrases[0]}"

    if len(phrases) >= 2:
        features += f", featuring {phrases[1]}"

    if len(phrases) >= 3:
        features += f", with {phrases[2]}. "
    else:
        features += ". "

    if len(phrases) >= 4:
        features += f"Perfect for {phrases[3]}"

        if len(phrases) >= 5:
            features += f", ideal as {phrases[4]}"

        if len(phrases) >= 6:
            features += f", and great for {phrases[5]}. "
        else:
            features += ". "

    if len(phrases) >= 7:
        features += f"Includes {phrases[6]}"

        if len(phrases) >= 8:
            features += f", {phrases[7]}"

        if len(phrases) >= 9:
            features += f", and {phrases[8]}"

        features += " for complete satisfaction."

    return features


def _build_closing_paragraph(brand: str, keywords: List[Dict]) -> str:
    """
    Build closing paragraph with CTA.

    WHY: Closing = reinforce brand trust + remaining keywords
    WHY: Soft CTA without promotional language (forbidden)
    """
    phrases = [k['phrase'] for k in keywords[:5]]

    closing = f"At {brand}, we stand behind our products with confidence. "

    if phrases:
        closing += f"Whether you need {phrases[0]}"

        if len(phrases) > 1:
            closing += f", {phrases[1]}"

        if len(phrases) > 2:
            closing += f", or {phrases[2]}"

        closing += ", "

    closing += "this product is built to exceed your expectations. "
    closing += "Experience the difference that quality craftsmanship makes."

    return closing


def optimize_existing_description(description: str, keywords: List[Dict]) -> str:
    """
    Optimize existing description by injecting missing keywords.

    WHY: If you have manually written description, this adds SEO
    WHY: Maintains your voice while improving coverage
    """
    desc_lower = description.lower()

    # WHY: Find high-value keywords NOT in description
    missing_keywords = [
        k for k in keywords[:50]
        if k['relevancy'] > 0.25 and k['phrase'] not in desc_lower
    ]

    if not missing_keywords:
        return description

    # WHY: Append paragraph with missing keywords
    addon = "\n\nAdditional Features: "

    addon_phrases = [k['phrase'] for k in missing_keywords[:10]]
    addon += f"Perfect for {', '.join(addon_phrases[:5])}"

    if len(addon_phrases) > 5:
        addon += f". Also ideal for {', '.join(addon_phrases[5:])}"

    addon += "."

    # WHY: Check if we exceed 2000 chars
    if len(description + addon) <= 2000:
        return description + addon
    else:
        return description


# WHY: validate_description moved to validators.py
