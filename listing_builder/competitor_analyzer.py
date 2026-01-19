# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/competitor_analyzer.py
# Purpose: Find keyword gaps between your listing and competitors
# NOT for: Parsing CSVs (use cerebro_parser for that)

from typing import List, Dict, Set


def find_keyword_gaps(
    your_keywords: List[Dict],
    competitor_keywords: List[Dict],
    min_competitors: int = 3,
    max_gaps: int = 50
) -> List[Dict]:
    """
    Find high-value keywords competitors rank for but you don't have.

    WHY: Competitors already validated these keywords convert
    WHY: Gap = opportunity to capture traffic you're missing

    Args:
        your_keywords: From Data Dive CSV (your current keywords)
        competitor_keywords: From Cerebro CSV (competitor keywords)
        min_competitors: Minimum ASINs ranking (default 3 = proven keyword)
        max_gaps: Maximum gap keywords to return (default 50)

    Returns:
        List of gap keywords sorted by opportunity value
    """
    # WHY: Create set of your phrases for fast lookup
    your_phrases = {kw['phrase'].lower() for kw in your_keywords}

    # WHY: Find keywords NOT in your listing
    gaps = []
    for comp_kw in competitor_keywords:
        phrase = comp_kw['phrase'].lower()

        # WHY: Skip if you already have this keyword
        if phrase in your_phrases:
            continue

        # WHY: Skip if too few competitors rank (unproven)
        if comp_kw.get('competitors_count', 0) < min_competitors:
            continue

        # WHY: Calculate opportunity score (volume * competitors validation)
        opportunity_score = comp_kw['search_volume'] * (comp_kw.get('competitors_count', 1) / 10)

        gaps.append({
            'phrase': phrase,
            'search_volume': comp_kw['search_volume'],
            'competitors_count': comp_kw.get('competitors_count', 0),
            'opportunity_score': opportunity_score,
            'source': 'cerebro_gap'
        })

    # WHY: Sort by opportunity score (highest value first)
    gaps.sort(key=lambda x: x['opportunity_score'], reverse=True)

    # WHY: Return top N gaps only (avoid overwhelming)
    return gaps[:max_gaps]


def merge_gap_keywords_with_base(
    base_keywords: List[Dict],
    gap_keywords: List[Dict],
    gap_relevancy_penalty: float = 0.85
) -> List[Dict]:
    """
    Merge gap keywords into base keyword list with adjusted relevancy.

    WHY: Gap keywords are validated by competitors but need lower priority than proven keywords
    WHY: Apply penalty to avoid overwhelming base keywords

    Args:
        base_keywords: Your Data Dive keywords (high confidence)
        gap_keywords: Cerebro gap keywords (medium confidence)
        gap_relevancy_penalty: Multiply factor (default 0.85 = 15% penalty)

    Returns:
        Combined list with gap keywords added at adjusted relevancy
    """
    merged = base_keywords.copy()

    for gap_kw in gap_keywords:
        # WHY: Convert Cerebro data to Data Dive format
        # WHY: Estimate relevancy from search volume (higher volume = higher relevancy)
        estimated_relevancy = min(80, gap_kw['search_volume'] / 100)
        estimated_relevancy *= gap_relevancy_penalty

        # WHY: Estimate ranking juice (assume medium difficulty)
        estimated_juice = 50.0

        merged.append({
            'phrase': gap_kw['phrase'],
            'relevancy': estimated_relevancy,
            'ranking_juice': estimated_juice,
            'search_volume': gap_kw['search_volume'],
            'source': gap_kw.get('source', 'cerebro_gap')
        })

    # WHY: Re-sort by relevancy + ranking juice
    merged.sort(key=lambda x: (x['relevancy'] + x['ranking_juice']), reverse=True)

    print(f"✓ Merged: {len(base_keywords)} base + {len(gap_keywords)} gaps = {len(merged)} total")

    return merged


def analyze_competitor_overlap(
    your_keywords: List[Dict],
    competitor_keywords: List[Dict]
) -> Dict:
    """
    Analyze overlap between your keywords and competitors.

    WHY: Understand competitive position
    WHY: High overlap = you're covering the niche well
    WHY: Low overlap = missing opportunities

    Returns:
        Dict with: overlap_count, overlap_pct, gap_count, unique_yours_count
    """
    your_phrases = {kw['phrase'].lower() for kw in your_keywords}
    comp_phrases = {kw['phrase'].lower() for kw in competitor_keywords}

    overlap = your_phrases & comp_phrases
    gaps = comp_phrases - your_phrases
    unique_yours = your_phrases - comp_phrases

    overlap_pct = (len(overlap) / len(comp_phrases) * 100) if comp_phrases else 0

    return {
        'overlap_count': len(overlap),
        'overlap_pct': overlap_pct,
        'gap_count': len(gaps),
        'unique_yours_count': len(unique_yours),
        'total_competitor_keywords': len(comp_phrases)
    }
