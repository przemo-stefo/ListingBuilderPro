#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/csv_parser.py
# Purpose: Parse Data Dive CSV exports and extract keyword data
# NOT for: Processing other CSV formats or general file parsing

"""
Data Dive CSV Parser
Extracts keywords, relevancy, search volume, ranking juice from Data Dive exports.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any


def parse_datadive_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Parse Data Dive CSV and extract keyword data.

    WHY: Data Dive exports have specific column structure that needs parsing
    WHY: We need relevancy, phrase, ranking juice, search volume, indexation status

    Returns list of keyword dictionaries with cleaned data.
    """
    keywords = []
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # WHY: Extract relevancy as float (0.0-1.0 scale from Data Dive)
            relevancy = float(row.get('Relevancy', '0').replace(',', '.'))

            # WHY: Extract keyword phrase (main search term)
            phrase = row.get('Phrase', '').strip().lower()

            # WHY: Ranking juice = importance metric from Data Dive
            ranking_juice = int(row.get('Ranking Juice ®', '0').replace(',', ''))

            # WHY: Search volume = monthly searches on Amazon
            search_volume = int(row.get('Search Volume', '0').replace(',', ''))

            # WHY: Check if keyword is already indexed (EXACT, BROAD, PHRASE, NONE)
            my_listing_status = row.get('MY_LISTING', 'NONE').strip().upper()

            # WHY: Clean up phrase - remove invalid characters
            # WHY: Data Dive sometimes exports combined phrases with | or &
            if '|' in phrase or '&' in phrase or ',' in phrase:
                continue  # WHY: Skip combined/invalid phrases

            # WHY: Skip phrases longer than 6 words (too specific, not useful)
            word_count = len(phrase.split())
            if word_count > 6 or word_count < 2:
                continue

            # WHY: Only include keywords with some relevancy (>0.1) or high search volume
            if relevancy > 0.1 or search_volume > 100:
                keywords.append({
                    'phrase': phrase,
                    'relevancy': relevancy,
                    'ranking_juice': ranking_juice,
                    'search_volume': search_volume,
                    'indexed': my_listing_status != 'NONE',
                    'index_type': my_listing_status,
                    'word_count': word_count
                })

    # WHY: Sort by relevancy DESC, then ranking juice DESC
    # WHY: Most relevant keywords should be prioritized in title/bullets
    keywords.sort(key=lambda k: (k['relevancy'], k['ranking_juice']), reverse=True)

    return keywords


def get_top_keywords(keywords: List[Dict], limit: int = 200) -> List[Dict]:
    """
    Get top N keywords by relevancy and ranking juice.

    WHY: Amazon algorithm focuses on top keywords for ranking
    WHY: From transcripts: Focus on most relevant keywords first
    """
    return keywords[:limit]


def filter_by_word_count(keywords: List[Dict], min_words: int = 2, max_words: int = 5) -> List[Dict]:
    """
    Filter keywords by word count.

    WHY: 2-5 word phrases are best for EXACT matches in title
    WHY: Single words are too broad, 6+ words too long for title
    """
    return [k for k in keywords if min_words <= k['word_count'] <= max_words]


def get_exact_phrases(keywords: List[Dict], limit: int = 20) -> List[str]:
    """
    Extract top phrases for EXACT matching.

    WHY: EXACT matches in title give strongest ranking boost
    WHY: From transcripts: 7-9 EXACT phrases in aggressive mode
    """
    # WHY: Prioritize 2-4 word phrases (best for title EXACT matches)
    filtered = filter_by_word_count(keywords, 2, 4)

    return [k['phrase'] for k in filtered[:limit]]


def calculate_coverage_target(keywords: List[Dict]) -> Dict[str, int]:
    """
    Calculate coverage targets based on keyword count.

    WHY: From transcripts: 96-98% coverage for aggressive mode
    WHY: Standard mode = 80-85%, Aggressive = 96-98%
    """
    total = len(keywords)

    return {
        'total_keywords': total,
        'standard_target': int(total * 0.82),  # WHY: 82% for standard
        'aggressive_target': int(total * 0.97)  # WHY: 97% for aggressive
    }
