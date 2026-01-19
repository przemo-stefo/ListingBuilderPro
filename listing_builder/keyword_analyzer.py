#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/keyword_analyzer.py
# Purpose: Analyze keywords, extract root words, calculate attribution
# NOT for: General text analysis or NLP tasks

"""
Keyword Analyzer
Extracts root words, analyzes keyword relationships, calculates Amazon attribution.
"""

from typing import List, Dict, Set
from collections import defaultdict


def extract_root_words(keywords: List[Dict]) -> Dict[str, List[str]]:
    """
    Extract root words and group related keywords.

    WHY: From transcripts - Amazon gives attribution by ROOT WORD
    WHY: Optimizing one root helps ALL keywords in that root
    WHY: "Focus on one relevant root at a time" - transcript principle
    """
    roots = defaultdict(list)

    for kw in keywords:
        phrase = kw['phrase']
        words = phrase.split()

        # WHY: Extract potential root words (2+ char, not common words)
        for word in words:
            if len(word) >= 2 and word not in STOP_WORDS:
                roots[word].append(phrase)

    # WHY: Sort by number of related keywords (most impactful roots first)
    return dict(sorted(roots.items(), key=lambda x: len(x[1]), reverse=True))


def find_keyword_combinations(keywords: List[Dict], max_length: int = 4) -> List[str]:
    """
    Find high-value keyword combinations for title.

    WHY: Title should have 7-9 EXACT phrases (aggressive mode)
    WHY: Combinations help cover multiple keywords with fewer words
    """
    phrases = [k['phrase'] for k in keywords if k['word_count'] <= max_length]

    # WHY: Prioritize phrases with high relevancy + ranking juice
    scored_phrases = [
        (p, keywords[i]['relevancy'] * keywords[i]['ranking_juice'])
        for i, p in enumerate(phrases) if i < len(keywords)
    ]

    scored_phrases.sort(key=lambda x: x[1], reverse=True)

    return [p[0] for p in scored_phrases]


def calculate_keyword_score(keyword: Dict) -> float:
    """
    Calculate composite score for keyword priority.

    WHY: Need single metric to prioritize keywords
    WHY: Combines relevancy (0-1) + normalized ranking juice + search volume
    """
    # WHY: Weight relevancy highest (from Data Dive)
    relevancy_score = keyword['relevancy'] * 1000

    # WHY: Ranking juice = DataDive proprietary metric
    juice_score = keyword['ranking_juice'] / 10000

    # WHY: Search volume = demand indicator
    volume_score = keyword['search_volume'] / 1000

    return relevancy_score + juice_score + volume_score


def group_by_relevancy_tier(keywords: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group keywords into tiers by relevancy.

    WHY: From transcripts - focus on HIGH relevancy keywords first
    WHY: Tier 1 (>0.4) = must include in title
    WHY: Tier 2 (0.3-0.4) = bullets and backend
    WHY: Tier 3 (<0.3) = backend only
    """
    tiers = {
        'tier1_title': [],      # WHY: >0.4 = highest relevancy, MUST be in title
        'tier2_bullets': [],    # WHY: 0.3-0.4 = strong keywords for bullets
        'tier3_backend': []     # WHY: <0.3 = backend search terms only
    }

    for kw in keywords:
        rel = kw['relevancy']

        if rel >= 0.4:
            tiers['tier1_title'].append(kw)
        elif rel >= 0.3:
            tiers['tier2_bullets'].append(kw)
        else:
            tiers['tier3_backend'].append(kw)

    return tiers


def detect_forbidden_keywords(keywords: List[Dict]) -> List[str]:
    """
    Detect potentially forbidden keywords.

    WHY: From transcripts - forbidden keywords cause SHADOW BLOCKS
    WHY: "non-toxic" caused massive de-indexing for a seller
    WHY: Gift keywords, health claims = common blocks
    """
    forbidden_patterns = {
        'non-toxic', 'non toxic', 'nontoxic',
        'bpa free', 'bpa-free',
        'gift', 'present',  # WHY: Gift keywords restricted in many categories
        'medical', 'therapeutic', 'cure', 'treat',  # WHY: Health claims
        'amazon', 'prime'  # WHY: Brand names forbidden
    }

    found_forbidden = []

    for kw in keywords:
        phrase = kw['phrase'].lower()

        for pattern in forbidden_patterns:
            if pattern in phrase:
                found_forbidden.append(phrase)
                break

    return found_forbidden


# WHY: Common stop words to exclude from root word extraction
# WHY: These don't contribute to Amazon ranking
STOP_WORDS = {
    'for', 'with', 'and', 'the', 'of', 'to', 'in', 'on', 'a', 'an',
    'is', 'it', 'that', 'this', 'by', 'at', 'from', 'or', 'as'
}
