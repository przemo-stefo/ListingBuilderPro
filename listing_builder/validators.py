#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/validators.py
# Purpose: Validation functions for all listing components
# NOT for: Data processing or content generation

"""
Validators
Validates title, bullets, backend, description against Amazon requirements.
"""

from typing import Dict, List
from text_utils import PROMO_WORDS


def validate_title(title: str) -> Dict[str, any]:
    """
    Validate title against Amazon requirements.

    WHY: Amazon has strict title requirements
    WHY: Violations = suppressed listings or account issues
    """
    issues = []

    # WHY: Amazon title max = 200 chars (most categories)
    if len(title) > 200:
        issues.append(f"Title too long: {len(title)} chars (max 200)")

    # WHY: Amazon requires titles (min 20 chars realistic)
    if len(title) < 20:
        issues.append("Title too short (min 20 chars recommended)")

    # WHY: Check for promotional words (forbidden)
    for word in PROMO_WORDS:
        if word in title.lower():
            issues.append(f"Promotional word detected: '{word}'")

    # WHY: Check for excessive capitalization (looks spammy)
    if sum(1 for c in title if c.isupper()) / len(title) > 0.5:
        issues.append("Excessive capitalization detected")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'length': len(title),
        'char_utilization': round((len(title) / 200) * 100, 1)
    }


def validate_bullets(bullets: List[str]) -> Dict[str, any]:
    """
    Validate bullets against Amazon requirements.

    WHY: Amazon has bullet requirements per category
    WHY: Most categories = 5 bullets, 500 chars each (some 1000)
    """
    issues = []

    # WHY: Check bullet count (most categories require 5)
    if len(bullets) < 5:
        issues.append(f"Only {len(bullets)} bullets (5 recommended)")

    # WHY: Check individual bullet length
    for i, bullet in enumerate(bullets):
        if len(bullet) > 500:
            issues.append(f"Bullet {i+1} too long: {len(bullet)} chars (max 500 for most categories)")

        if len(bullet) < 50:
            issues.append(f"Bullet {i+1} too short: {len(bullet)} chars (min 50 recommended)")

    # WHY: Check for promotional language (forbidden)
    for bullet in bullets:
        for promo in PROMO_WORDS:
            if promo in bullet.lower():
                issues.append(f"Promotional language detected: '{promo}'")
                break  # WHY: Only report once per bullet

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'bullet_count': len(bullets),
        'avg_length': sum(len(b) for b in bullets) // len(bullets) if bullets else 0
    }


def validate_backend(backend: str) -> Dict[str, any]:
    """
    Validate backend search terms against Amazon rules.

    WHY: Amazon has strict backend requirements
    WHY: Violations = reduced indexing or listing suppression
    """
    issues = []

    byte_size = len(backend.encode('utf-8'))

    # WHY: Amazon hard limit = 250 bytes
    if byte_size > 250:
        issues.append(f"Backend too long: {byte_size} bytes (max 250)")

    # WHY: Check for forbidden punctuation
    forbidden_chars = [',', '.', '!', '?', ';', ':', '"', "'"]
    for char in forbidden_chars:
        if char in backend:
            issues.append(f"Forbidden character detected: '{char}'")
            break  # WHY: Only report once

    # WHY: Check for ASIN-like strings (forbidden)
    words = backend.split()
    for word in words:
        if len(word) == 10 and word.startswith('B0'):
            issues.append(f"Possible ASIN detected: {word}")
            break

    # WHY: Check for excessive repetition (spam detection)
    # WHY: Aggressive mode limit = ≤5× per word
    word_counts = {}
    for word in words:
        if len(word) > 2:  # WHY: Ignore very short words
            word_counts[word] = word_counts.get(word, 0) + 1

    for word, count in word_counts.items():
        if count > 5:  # WHY: >5× = spam flag
            issues.append(f"Word '{word}' repeated {count} times (max 5 recommended)")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'byte_size': byte_size,
        'utilization': round((byte_size / 250) * 100, 1)
    }


def validate_description(description: str) -> Dict[str, any]:
    """
    Validate description against Amazon rules.

    WHY: Amazon has description requirements
    WHY: 2000 char limit, no promotional language
    """
    issues = []

    # WHY: Check length
    if len(description) > 2000:
        issues.append(f"Description too long: {len(description)} chars (max 2000)")

    if len(description) < 200:
        issues.append("Description too short (min 200 chars recommended)")

    # WHY: Check for promotional language
    for promo in PROMO_WORDS:
        if promo in description.lower():
            issues.append(f"Promotional language detected: '{promo}'")
            break  # WHY: Only report once

    # WHY: Check for external links (forbidden)
    if 'http://' in description or 'https://' in description or 'www.' in description:
        issues.append("External links detected (forbidden)")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'char_count': len(description),
        'utilization': round((len(description) / 2000) * 100, 1)
    }
