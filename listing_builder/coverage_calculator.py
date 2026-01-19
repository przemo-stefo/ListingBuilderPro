#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/coverage_calculator.py
# Purpose: Calculate keyword coverage percentage across listing
# NOT for: Competitive analysis or external data

"""
Coverage Calculator
Calculates keyword coverage % across title, bullets, description, backend.
Target: 82% standard, 96-98% aggressive.
"""

from typing import List, Dict, Set


def calculate_coverage(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    description: str,
    backend: str
) -> Dict[str, any]:
    """
    Calculate keyword coverage across entire listing.

    WHY: From transcripts - target 82% standard, 96-98% aggressive
    WHY: Coverage = % of keywords indexed somewhere in listing
    WHY: Amazon indexes title, bullets, description, backend differently
    """
    # WHY: Combine all listing text
    listing_text = _combine_listing_text(title, bullets, description, backend)

    # WHY: Calculate coverage for top 200 keywords (standard benchmark)
    top_200 = keywords[:200]

    covered_count = 0
    covered_keywords = []
    missing_keywords = []

    for kw in top_200:
        phrase = kw['phrase']

        # WHY: Check if ANY word from phrase appears in listing (lenient matching)
        if _is_keyword_covered(phrase, listing_text):
            covered_count += 1
            covered_keywords.append(phrase)
        else:
            missing_keywords.append(phrase)

    # WHY: Calculate coverage percentage
    coverage_pct = (covered_count / len(top_200)) * 100 if top_200 else 0

    # WHY: Determine mode based on coverage
    if coverage_pct >= 96:
        mode = "AGGRESSIVE"  # WHY: 96-98% = aggressive optimization
    elif coverage_pct >= 82:
        mode = "STANDARD"    # WHY: 82-85% = standard optimization
    else:
        mode = "UNDEROPTIMIZED"  # WHY: <82% = needs work

    return {
        'coverage_pct': round(coverage_pct, 1),
        'covered_count': covered_count,
        'total_keywords': len(top_200),
        'mode': mode,
        'covered_keywords': covered_keywords[:20],  # WHY: First 20 for review
        'missing_keywords': missing_keywords[:20]   # WHY: First 20 to add
    }


def calculate_section_coverage(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    backend: str
) -> Dict[str, float]:
    """
    Calculate coverage by listing section.

    WHY: Understand where keywords are indexed
    WHY: Title = strongest indexing, bullets = second, backend = weakest
    """
    top_200 = keywords[:200]

    title_text = title.lower()
    bullets_text = ' '.join(bullets).lower()
    backend_text = backend.lower()

    title_covered = sum(1 for k in top_200 if _is_keyword_covered(k['phrase'], title_text))
    bullets_covered = sum(1 for k in top_200 if _is_keyword_covered(k['phrase'], bullets_text))
    backend_covered = sum(1 for k in top_200 if _is_keyword_covered(k['phrase'], backend_text))

    return {
        'title_coverage': round((title_covered / len(top_200)) * 100, 1),
        'bullets_coverage': round((bullets_covered / len(top_200)) * 100, 1),
        'backend_coverage': round((backend_covered / len(top_200)) * 100, 1)
    }


def calculate_exact_match_count(keywords: List[Dict], title: str) -> int:
    """
    Count EXACT phrase matches in title.

    WHY: From transcripts - aggressive mode targets 7-9 EXACT phrases
    WHY: EXACT matches = strongest ranking signal
    """
    title_lower = title.lower()

    exact_matches = 0

    # WHY: Check top 30 keywords for EXACT matches
    for kw in keywords[:30]:
        phrase = kw['phrase']

        # WHY: EXACT match = full phrase appears in title
        if phrase in title_lower:
            exact_matches += 1

    return exact_matches


def _combine_listing_text(
    title: str,
    bullets: List[str],
    description: str,
    backend: str
) -> str:
    """
    Combine all listing text into single searchable string.

    WHY: Need unified text for coverage calculation
    WHY: Lowercase for case-insensitive matching
    """
    all_text = title + ' ' + ' '.join(bullets) + ' ' + description + ' ' + backend
    return all_text.lower()


def _is_keyword_covered(phrase: str, text: str) -> bool:
    """
    Check if keyword is covered in text (lenient matching).

    WHY: Lenient = if 70%+ of words present, consider covered
    WHY: Amazon's algorithm uses tokenized matching, not exact phrases
    WHY: "cutting board set" covered if "cutting" + "board" + "set" all present
    """
    phrase_words = phrase.lower().split()
    text_words = set(text.split())

    # WHY: Count how many phrase words appear in text
    matched_words = sum(1 for word in phrase_words if word in text_words)

    # WHY: Consider covered if 70%+ words matched
    match_ratio = matched_words / len(phrase_words)

    return match_ratio >= 0.7


# WHY: analyze_repetition and generate_coverage_report moved to reporting.py
