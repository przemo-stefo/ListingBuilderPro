#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/bullet_generator.py
# Purpose: Generate optimized bullet points with keyword coverage
# NOT for: Descriptions, A+ content, or other listing elements

"""
Bullet Point Generator
Creates 5 optimized bullets with keyword coverage and benefit-focused copy.
"""

from typing import List, Dict, Tuple
from text_utils import filter_promo_phrases


def generate_bullets(
    keywords: List[Dict],
    title: str,
    product_benefits: List[str] = None,
    char_limit: int = 500
) -> Tuple[List[str], Dict]:
    """
    Generate 5 optimized bullet points.

    WHY: Amazon allows 5 bullets, each up to 500 chars
    WHY: Bullets = second most important after title for indexing
    WHY: From transcripts - second image + first bullet = critical for conversion
    WHY: Answer buyer's main question in first bullet
    """
    bullets = []

    # WHY: Use tier 2 keywords (0.3-0.4 relevancy) - strong but not title-worthy
    tier2_keywords = [k for k in keywords if 0.3 <= k['relevancy'] < 0.4]

    # WHY: Also include tier 1 keywords not in title (for reinforcement)
    title_lower = title.lower()
    tier1_not_in_title = [
        k for k in keywords
        if k['relevancy'] >= 0.4 and k['phrase'] not in title_lower
    ]

    bullet_keywords = tier1_not_in_title[:10] + tier2_keywords[:20]

    # WHY: Filter out promotional words from bullet keywords
    bullet_phrases = [k['phrase'] for k in bullet_keywords]
    bullet_phrases = filter_promo_phrases(bullet_phrases)

    # WHY: Rebuild bullet_keywords with filtered phrases
    filtered_bullet_keywords = [k for k in bullet_keywords if k['phrase'] in bullet_phrases]

    # WHY: 5 bullets = Amazon standard
    bullet_themes = [
        "PREMIUM QUALITY",      # WHY: Material, construction, durability
        "PRACTICAL DESIGN",     # WHY: Size, features, functionality
        "VERSATILE USE",        # WHY: Use cases, applications
        "EASY CARE",           # WHY: Maintenance, cleaning, storage
        "PERFECT GIFT"         # WHY: Gift occasions, satisfaction guarantee
    ]

    for i, theme in enumerate(bullet_themes):
        # WHY: Each bullet targets different keyword subset
        bullet_kws = filtered_bullet_keywords[i*4:(i+1)*4]

        bullet_text = _create_bullet(theme, bullet_kws, char_limit)
        bullets.append(bullet_text)

    stats = {
        'bullet_count': len(bullets),
        'avg_length': sum(len(b) for b in bullets) // len(bullets),
        'total_chars': sum(len(b) for b in bullets),
        'keywords_covered': len(filtered_bullet_keywords)
    }

    return bullets, stats


def _create_bullet(theme: str, keywords: List[Dict], char_limit: int) -> str:
    """
    Create single bullet with theme and keywords.

    WHY: Structure = THEME: benefit, benefit, benefit with natural keyword integration
    WHY: Front-load benefits (buyers skim)
    WHY: Natural language > keyword stuffing
    """
    # WHY: Extract keyword phrases
    phrases = [k['phrase'] for k in keywords[:4]]

    # WHY: Build benefit-focused copy
    if theme == "PREMIUM QUALITY":
        bullet = f"✓ PREMIUM QUALITY – Made from {phrases[0] if phrases else 'premium materials'}"
        if len(phrases) > 1:
            bullet += f", featuring {phrases[1]}"
        if len(phrases) > 2:
            bullet += f". Perfect {phrases[2]} for long-lasting durability and performance"

    elif theme == "PRACTICAL DESIGN":
        bullet = f"✓ PRACTICAL DESIGN – Designed as {phrases[0] if phrases else 'practical tool'}"
        if len(phrases) > 1:
            bullet += f" with {phrases[1]}"
        if len(phrases) > 2:
            bullet += f". Ideal {phrases[2]} for everyday use"

    elif theme == "VERSATILE USE":
        bullet = f"✓ VERSATILE – Perfect for {phrases[0] if phrases else 'multiple uses'}"
        if len(phrases) > 1:
            bullet += f", {phrases[1]}"
        if len(phrases) > 2:
            bullet += f", and {phrases[2]}"
        bullet += ". Suitable for any occasion"

    elif theme == "EASY CARE":
        bullet = f"✓ EASY CARE – Simple maintenance for {phrases[0] if phrases else 'your product'}"
        if len(phrases) > 1:
            bullet += f". Safe for {phrases[1]}"
        bullet += ". Easy cleaning and convenient storage"  # WHY: Changed from "Hassle-free" (contains promo word)

    else:  # PERFECT GIFT
        bullet = f"✓ PERFECT GIFT – Ideal {phrases[0] if phrases else 'gift'} for any occasion"
        if len(phrases) > 1:
            bullet += f". Great {phrases[1]}"
        bullet += ". Complete customer satisfaction"  # WHY: Changed from "guaranteed" (promo word)

    # WHY: Truncate if exceeds char limit
    if len(bullet) > char_limit:
        bullet = bullet[:char_limit-3] + "..."

    return bullet


def generate_feature_bullets(
    keywords: List[Dict],
    features: List[str]
) -> List[str]:
    """
    Generate bullets from specific product features.

    WHY: Use when you have detailed product feature list
    WHY: Combines features with keyword optimization
    """
    bullets = []

    for i, feature in enumerate(features[:5]):  # WHY: Max 5 bullets
        # WHY: Get relevant keywords for this feature
        feature_words = set(feature.lower().split())
        relevant_kws = [
            k for k in keywords
            if any(word in k['phrase'] for word in feature_words)
        ][:3]

        # WHY: Integrate keywords naturally into feature
        if relevant_kws:
            kw_phrases = ', '.join(k['phrase'] for k in relevant_kws[:2])
            bullet = f"✓ {feature} - Perfect for {kw_phrases}"
        else:
            bullet = f"✓ {feature}"

        bullets.append(bullet)

    return bullets


def optimize_bullet_keywords(bullets: List[str], keywords: List[Dict]) -> List[str]:
    """
    Optimize existing bullets by injecting high-value keywords.

    WHY: If you have manually written bullets, this adds missing keywords
    WHY: Maintains your voice while improving SEO
    """
    optimized = []

    # WHY: Extract words already in bullets
    bullet_text = ' '.join(bullets).lower()
    used_words = set(bullet_text.split())

    # WHY: Find high-value keywords NOT in bullets
    missing_keywords = [
        k for k in keywords[:30]
        if k['relevancy'] > 0.35 and k['phrase'] not in bullet_text
    ]

    for i, bullet in enumerate(bullets):
        # WHY: Try to inject 1-2 missing keywords per bullet
        if i < len(missing_keywords):
            kw = missing_keywords[i]['phrase']

            # WHY: Append keyword naturally
            if not bullet.endswith('.'):
                bullet += '.'

            bullet += f" Features {kw} for enhanced performance."

        optimized.append(bullet)

    return optimized


# WHY: validate_bullets moved to validators.py
