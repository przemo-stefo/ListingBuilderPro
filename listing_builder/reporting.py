#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/reporting.py
# Purpose: Generate reports and analyze listing quality
# NOT for: Core calculation logic

"""
Reporting & Analysis
Generate human-readable reports and analyze listing quality metrics.
"""

from typing import List, Dict


def analyze_repetition(
    title: str,
    bullets: List[str],
    backend: str
) -> Dict[str, any]:
    """
    Analyze keyword repetition across listing.

    WHY: From transcripts - anti-stuffing limits:
    WHY: Title: ≤3× same word
    WHY: Entire listing (aggressive): ≤5× same word
    WHY: Excessive repetition = spam detection
    """
    # WHY: Combine all text
    all_text = title + ' ' + ' '.join(bullets) + ' ' + backend
    words = all_text.lower().split()

    # WHY: Count word frequency
    word_counts = {}
    for word in words:
        if len(word) > 2:  # WHY: Ignore very short words
            word_counts[word] = word_counts.get(word, 0) + 1

    # WHY: Find overused words
    overused = {
        word: count for word, count in word_counts.items()
        if count > 5  # WHY: >5× = potential spam flag
    }

    # WHY: Check title repetition
    title_words = title.lower().split()
    title_counts = {}
    for word in title_words:
        if len(word) > 2:
            title_counts[word] = title_counts.get(word, 0) + 1

    title_overused = {
        word: count for word, count in title_counts.items()
        if count > 3  # WHY: >3× in title = stuffing
    }

    return {
        'overused_in_listing': overused,
        'overused_in_title': title_overused,
        'total_unique_words': len(word_counts),
        'avg_repetition': sum(word_counts.values()) / len(word_counts) if word_counts else 0
    }


def generate_coverage_report(
    keywords: List[Dict],
    title: str,
    bullets: List[str],
    description: str,
    backend: str
) -> str:
    """
    Generate human-readable coverage report.

    WHY: Quick summary for user to understand listing performance
    """
    # WHY: Import here to avoid circular dependency
    from coverage_calculator import (
        calculate_coverage, calculate_section_coverage,
        calculate_exact_match_count
    )

    coverage = calculate_coverage(keywords, title, bullets, description, backend)
    section_cov = calculate_section_coverage(keywords, title, bullets, backend)
    exact_matches = calculate_exact_match_count(keywords, title)
    repetition = analyze_repetition(title, bullets, backend)

    report = f"""
KEYWORD COVERAGE REPORT
{'='*50}

Overall Coverage: {coverage['coverage_pct']}% ({coverage['covered_count']}/{coverage['total_keywords']} keywords)
Mode: {coverage['mode']}

Section Breakdown:
  • Title: {section_cov['title_coverage']}%
  • Bullets: {section_cov['bullets_coverage']}%
  • Backend: {section_cov['backend_coverage']}%

Title EXACT Matches: {exact_matches} phrases

Top Missing Keywords (add to backend):
"""

    for kw in coverage['missing_keywords'][:10]:
        report += f"  • {kw}\n"

    if repetition['overused_in_listing']:
        report += "\n⚠️  Overused Words (potential spam):\n"
        for word, count in list(repetition['overused_in_listing'].items())[:5]:
            report += f"  • '{word}' used {count}× (max 5 recommended)\n"

    return report


def print_validation_results(
    title_validation: dict,
    bullet_validation: dict,
    backend_validation: dict,
    desc_validation: dict
):
    """
    Print validation results with formatted output.

    WHY: Extracted from listing_optimizer.py to reduce line count
    WHY: Centralize validation reporting logic
    """
    all_valid = (
        title_validation['valid'] and
        bullet_validation['valid'] and
        backend_validation['valid'] and
        desc_validation['valid']
    )

    if all_valid:
        print("   ✓ All components valid!\n")
        return True

    print("   ⚠️  Validation issues detected:\n")
    if not title_validation['valid']:
        for issue in title_validation['issues']:
            print(f"      TITLE: {issue}")
    if not bullet_validation['valid']:
        for issue in bullet_validation['issues']:
            print(f"      BULLETS: {issue}")
    if not backend_validation['valid']:
        for issue in backend_validation['issues']:
            print(f"      BACKEND: {issue}")
    if not desc_validation['valid']:
        for issue in desc_validation['issues']:
            print(f"      DESCRIPTION: {issue}")
    print()

    return False
