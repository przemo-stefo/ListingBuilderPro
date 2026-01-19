# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/keyword_expander.py
# Purpose: Expand keywords with variations, synonyms, and merge multiple Data Dive files
# NOT for: Parsing CSVs (use magnet_parser for that)

from typing import List, Dict, Set


def expand_with_magnet_variations(
    base_keywords: List[Dict],
    magnet_keywords: List[Dict],
    max_additions: int = 30
) -> List[Dict]:
    """
    Expand base keywords with Magnet variations.

    WHY: Magnet finds related terms Data Dive might miss
    WHY: Synonyms capture different customer search behaviors

    Args:
        base_keywords: Your Data Dive keywords (primary source)
        magnet_keywords: Helium 10 Magnet variations
        max_additions: Max variations to add (default 30)

    Returns:
        Expanded keyword list with variations added
    """
    # WHY: Create set of existing phrases to avoid duplicates
    existing_phrases = {kw['phrase'].lower() for kw in base_keywords}

    variations = []
    for mag_kw in magnet_keywords:
        phrase = mag_kw['phrase'].lower()

        # WHY: Skip if already in base keywords
        if phrase in existing_phrases:
            continue

        # WHY: Convert Magnet data to Data Dive format
        # WHY: Variations get lower relevancy than base keywords
        estimated_relevancy = min(75, mag_kw['search_volume'] / 150)

        # WHY: Smart Score boosts relevancy (if available)
        if mag_kw.get('smart_score', 0) >= 7:
            estimated_relevancy += 10
        elif mag_kw.get('smart_score', 0) >= 5:
            estimated_relevancy += 5

        variations.append({
            'phrase': phrase,
            'relevancy': estimated_relevancy,
            'ranking_juice': 50.0,  # WHY: Assume medium difficulty
            'search_volume': mag_kw['search_volume'],
            'source': 'magnet_variation'
        })

    # WHY: Sort by relevancy and limit additions
    variations.sort(key=lambda x: x['relevancy'], reverse=True)
    variations = variations[:max_additions]

    # WHY: Merge with base
    expanded = base_keywords + variations

    print(f"✓ Expanded: {len(base_keywords)} base + {len(variations)} variations = {len(expanded)} total")

    return expanded


def merge_multiple_datadive_files(
    datadive_keywords_list: List[List[Dict]],
    merge_strategy: str = 'union'
) -> List[Dict]:
    """
    Merge multiple Data Dive CSV exports for comparison/combination.

    WHY: Compare different products in same niche
    WHY: Combine keywords from related products
    WHY: Find common high-value keywords across products

    Args:
        datadive_keywords_list: List of keyword lists from different Data Dive exports
        merge_strategy: 'union' (all keywords) or 'intersection' (only shared)

    Returns:
        Merged keyword list
    """
    if not datadive_keywords_list:
        return []

    if len(datadive_keywords_list) == 1:
        return datadive_keywords_list[0]

    if merge_strategy == 'intersection':
        return _merge_intersection(datadive_keywords_list)
    else:
        return _merge_union(datadive_keywords_list)


def _merge_union(datadive_keywords_list: List[List[Dict]]) -> List[Dict]:
    """Merge using UNION (all keywords). WHY: Complete keyword universe."""
    return _merge_keywords(datadive_keywords_list, mode='union')


def _merge_intersection(datadive_keywords_list: List[List[Dict]]) -> List[Dict]:
    """Merge using INTERSECTION (shared only). WHY: High-confidence core keywords."""
    return _merge_keywords(datadive_keywords_list, mode='intersection')


def _merge_keywords(datadive_keywords_list: List[List[Dict]], mode: str) -> List[Dict]:
    """
    Merge keyword lists with union or intersection strategy.

    WHY: Unified merge logic for both strategies (DRY principle)
    WHY: Averages scores when same keyword appears in multiple files
    """
    # WHY: For intersection, first find common phrases
    common_phrases = None
    if mode == 'intersection':
        phrase_sets = [{kw['phrase'].lower() for kw in kw_list} for kw_list in datadive_keywords_list]
        common_phrases = set.intersection(*phrase_sets)

    # WHY: Group all occurrences of same phrase
    keyword_map = {}
    for kw_list in datadive_keywords_list:
        for kw in kw_list:
            phrase = kw['phrase'].lower()
            # WHY: For intersection, skip if not in common set
            if common_phrases and phrase not in common_phrases:
                continue
            if phrase not in keyword_map:
                keyword_map[phrase] = []
            keyword_map[phrase].append(kw)

    # WHY: Average scores when keyword appears in multiple files
    merged = []
    for phrase, occurrences in keyword_map.items():
        avg_relevancy = sum(kw['relevancy'] for kw in occurrences) / len(occurrences)
        avg_juice = sum(kw['ranking_juice'] for kw in occurrences) / len(occurrences)
        max_volume = max(kw.get('search_volume', 0) for kw in occurrences)

        merged.append({
            'phrase': phrase,
            'relevancy': avg_relevancy,
            'ranking_juice': avg_juice,
            'search_volume': max_volume,
            'source': f'merged_{mode}'
        })

    # WHY: Sort by relevancy + ranking juice
    merged.sort(key=lambda x: (x['relevancy'] + x['ranking_juice']), reverse=True)

    # WHY: Print appropriate message
    if mode == 'union':
        print(f"✓ Merged (union): {sum(len(kl) for kl in datadive_keywords_list)} keywords → {len(merged)} unique")
    else:
        print(f"✓ Merged (intersection): {len(merged)} shared keywords across {len(datadive_keywords_list)} files")

    return merged


def apply_search_volume_filter(
    keywords: List[Dict],
    min_search_volume: int
) -> List[Dict]:
    """
    Filter keywords by minimum search volume.

    WHY: Focus character budget on high-traffic keywords
    WHY: Skip ultra-low volume terms (<50-100 searches/month)

    Args:
        min_search_volume: Minimum monthly searches threshold
    """
    if min_search_volume <= 0:
        return keywords

    filtered = [kw for kw in keywords if kw.get('search_volume', 0) >= min_search_volume]

    print(f"✓ Volume filter: {len(keywords)} keywords → {len(filtered)} above {min_search_volume} searches/month")

    return filtered
