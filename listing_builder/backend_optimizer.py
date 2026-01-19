#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/backend_optimizer.py
# Purpose: Optimize backend search terms using greedy packing algorithm
# NOT for: Frontend content or visible listing elements

"""
Backend Search Terms Optimizer
Uses greedy algorithm to pack 240-249 bytes of backend keywords.
Maximizes keyword coverage within Amazon's 250 byte limit.
"""

from typing import List, Dict, Set, Tuple


def optimize_backend_keywords(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    max_bytes: int = 249
) -> Tuple[str, Dict]:
    """
    Pack backend keywords using greedy algorithm (240-249 bytes).

    WHY: Amazon backend = 250 byte limit (strict)
    WHY: From transcripts - aggressive mode targets 240-249 bytes (96-99% utilization)
    WHY: Greedy packing = maximum keyword coverage
    WHY: Don't repeat keywords already in title/bullets

    Returns: (backend_string, stats_dict)
    """
    # WHY: Extract all words already used in frontend (title + bullets)
    used_words = _extract_used_words(title, bullets)

    # WHY: Get candidate keywords not yet used
    backend_candidates = _get_backend_candidates(keywords, used_words)

    # WHY: Greedy pack to maximize byte utilization
    packed_keywords = _greedy_pack(backend_candidates, max_bytes)

    # WHY: Join with spaces (Amazon's required format)
    backend_string = ' '.join(packed_keywords)

    # WHY: Calculate byte size (Amazon counts bytes, not chars)
    byte_size = len(backend_string.encode('utf-8'))

    stats = {
        'byte_size': byte_size,
        'utilization': round((byte_size / 250) * 100, 1),
        'keyword_count': len(packed_keywords),
        'unique_words': len(set(' '.join(packed_keywords).split()))
    }

    return backend_string, stats


def _extract_used_words(title: str, bullets: List[str]) -> Set[str]:
    """
    Extract all words already used in title and bullets.

    WHY: Don't repeat keywords in backend (wastes space)
    WHY: Amazon indexes title/bullets automatically
    WHY: Backend = NEW keywords not yet indexed
    """
    used = set()

    # WHY: Extract from title
    title_words = title.lower().replace('-', ' ').split()
    used.update(w.strip('.,!?()[]') for w in title_words if len(w) > 1)

    # WHY: Extract from bullets
    for bullet in bullets:
        bullet_words = bullet.lower().split()
        used.update(w.strip('.,!?()[]') for w in bullet_words if len(w) > 1)

    return used


def _get_backend_candidates(keywords: List[Dict], used_words: Set[str]) -> List[str]:
    """
    Get candidate keywords for backend (not already used).

    WHY: Only include keywords with new words
    WHY: Prioritize high relevancy + ranking juice
    WHY: Filter out keywords fully covered by frontend
    WHY: Filter non-English keywords
    """
    # WHY: Common Spanish words to filter out
    spanish_words = {'de', 'para', 'en', 'la', 'el', 'con', 'tabla', 'tablas', 'cocina', 'madera', 'bambu', 'picar'}

    candidates = []

    for kw in keywords:
        phrase = kw['phrase']
        phrase_words = set(phrase.split())

        # WHY: Skip if contains Spanish words (non-English keywords)
        if phrase_words & spanish_words:
            continue

        # WHY: Check if phrase has NEW words not in frontend
        new_words = phrase_words - used_words

        if new_words:  # WHY: At least one new word
            # WHY: Calculate value = new words coverage + relevancy
            value_score = len(new_words) * kw['relevancy']
            candidates.append((phrase, value_score, len(phrase)))

    # WHY: Sort by value score DESC (most valuable keywords first)
    candidates.sort(key=lambda x: x[1], reverse=True)

    return [c[0] for c in candidates]


def _greedy_pack(candidates: List[str], max_bytes: int) -> List[str]:
    """
    Greedy packing algorithm to maximize byte utilization.

    WHY: Greedy = add keywords in order until byte limit reached
    WHY: Target 240-249 bytes (96-99% utilization)
    WHY: Stop before exceeding 250 byte Amazon limit
    WHY: Enforce ≤5× repetition limit per word
    """
    packed = []
    current_bytes = 0
    word_counts = {}  # WHY: Track word repetition

    for keyword in candidates:
        # WHY: Calculate bytes if we add this keyword (+ space separator)
        keyword_bytes = len(keyword.encode('utf-8'))
        separator_bytes = 1 if packed else 0  # WHY: Space between keywords

        test_bytes = current_bytes + keyword_bytes + separator_bytes

        # WHY: Stop if we'd exceed max bytes
        if test_bytes > max_bytes:
            continue

        # WHY: Check repetition limit (≤5× per word in aggressive mode)
        keyword_words = keyword.split()
        would_violate = False

        for word in keyword_words:
            if len(word) > 2:  # WHY: Only check meaningful words
                if word_counts.get(word, 0) >= 5:
                    would_violate = True
                    break

        if would_violate:
            continue  # WHY: Skip this keyword to avoid spam detection

        # WHY: Add keyword and update counts
        packed.append(keyword)
        current_bytes = test_bytes

        for word in keyword_words:
            if len(word) > 2:
                word_counts[word] = word_counts.get(word, 0) + 1

        # WHY: If we're at 240+ bytes, we've hit target range
        if current_bytes >= 240:
            break

    return packed


# WHY: validate_backend moved to validators.py


def extract_misspellings(keywords: List[Dict]) -> List[str]:
    """
    Extract common misspellings for backend.

    WHY: Backend = great place for misspellings
    WHY: Captures traffic from users who misspell
    WHY: Don't put misspellings in frontend (looks unprofessional)
    """
    # WHY: Common patterns for misspellings
    misspelling_patterns = {
        'board': ['bord', 'bourd'],
        'cutting': ['cuting', 'cutti ng'],
        'kitchen': ['kitchn', 'kichen'],
        'bamboo': ['bambo', 'bambou'],
    }

    misspellings = []

    for kw in keywords[:50]:  # WHY: Check top 50 keywords only
        phrase = kw['phrase']

        for correct, misspelled_list in misspelling_patterns.items():
            if correct in phrase:
                for misspelled in misspelled_list:
                    misspelled_phrase = phrase.replace(correct, misspelled)
                    misspellings.append(misspelled_phrase)

    return misspellings[:20]  # WHY: Limit to 20 misspellings
