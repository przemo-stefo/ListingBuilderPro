# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/enhancements.py
# Purpose: Process optional CSV enhancements (Cerebro, Magnet, multi-file merging)
# NOT for: Core listing optimization (that's in listing_optimizer.py)

from typing import List, Dict


def process_enhancements(
    keywords: List[Dict],
    cerebro_csv: str = None,
    magnet_csv: str = None,
    additional_datadive_csvs: list = None,
    min_search_volume: int = 0,
    merge_strategy: str = 'union'
) -> List[Dict]:
    """
    Process all optional CSV enhancements and return enhanced keyword list.

    WHY: Centralize all enhancement logic in one place
    WHY: Keep listing_optimizer.py under 200 lines (David's philosophy)

    Args:
        keywords: Base keyword list from main Data Dive CSV
        cerebro_csv: Optional Cerebro CSV path
        magnet_csv: Optional Magnet CSV path
        additional_datadive_csvs: Optional list of additional Data Dive CSVs
        min_search_volume: Minimum search volume filter
        merge_strategy: 'union' or 'intersection' for multiple files

    Returns:
        Enhanced keyword list
    """
    # WHY: Merge additional Data Dive files if provided
    if additional_datadive_csvs:
        keywords = _merge_additional_datadive(keywords, additional_datadive_csvs, merge_strategy)

    # WHY: Apply search volume filter if specified
    if min_search_volume > 0:
        keywords = _apply_volume_filter(keywords, min_search_volume)

    # WHY: Add competitor gap keywords if Cerebro CSV provided
    if cerebro_csv:
        keywords = _add_cerebro_gaps(keywords, cerebro_csv, min_search_volume)

    # WHY: Expand with Magnet variations if provided
    if magnet_csv:
        keywords = _expand_with_magnet(keywords, magnet_csv, min_search_volume)

    return keywords


def _merge_additional_datadive(
    base_keywords: List[Dict],
    additional_csvs: list,
    merge_strategy: str
) -> List[Dict]:
    """
    Merge additional Data Dive CSV files.

    WHY: Support multi-product comparison and keyword discovery
    """
    from csv_parser import parse_datadive_csv
    from keyword_expander import merge_multiple_datadive_files

    all_keyword_lists = [base_keywords]

    for add_csv in additional_csvs:
        add_keywords = parse_datadive_csv(add_csv)
        all_keyword_lists.append(add_keywords)
        print(f"   ✓ Additional CSV: {len(add_keywords)} keywords")

    return merge_multiple_datadive_files(all_keyword_lists, merge_strategy)


def _apply_volume_filter(
    keywords: List[Dict],
    min_search_volume: int
) -> List[Dict]:
    """
    Filter keywords by minimum search volume.

    WHY: Focus character budget on high-traffic keywords
    """
    from keyword_expander import apply_search_volume_filter

    original_count = len(keywords)
    filtered = apply_search_volume_filter(keywords, min_search_volume)
    print(f"   ✓ Volume filter: {original_count} → {len(filtered)} keywords (≥{min_search_volume}/mo)")

    return filtered


def _add_cerebro_gaps(
    keywords: List[Dict],
    cerebro_csv: str,
    min_search_volume: int
) -> List[Dict]:
    """
    Add competitor gap keywords from Cerebro CSV.

    WHY: Find keywords competitors rank for that you're missing
    """
    from cerebro_parser import parse_cerebro_csv, filter_high_value_keywords
    from competitor_analyzer import find_keyword_gaps, merge_gap_keywords_with_base, analyze_competitor_overlap

    print("\n🔍 Competitor Gap Analysis...")

    cerebro_keywords = parse_cerebro_csv(cerebro_csv)
    high_value = filter_high_value_keywords(cerebro_keywords, min_search_volume=max(100, min_search_volume))

    overlap_analysis = analyze_competitor_overlap(keywords, high_value)
    print(f"   ✓ Overlap: {overlap_analysis['overlap_pct']:.1f}%")
    print(f"   ✓ Gaps found: {overlap_analysis['gap_count']}")

    gap_keywords = find_keyword_gaps(keywords, high_value, max_gaps=50)
    if gap_keywords:
        enhanced = merge_gap_keywords_with_base(keywords, gap_keywords)
        print(f"   ✓ Added {len(gap_keywords)} gap keywords\n")
        return enhanced

    return keywords


def _expand_with_magnet(
    keywords: List[Dict],
    magnet_csv: str,
    min_search_volume: int
) -> List[Dict]:
    """
    Expand keywords with Magnet variations.

    WHY: Add related terms and synonyms that Data Dive might miss
    """
    from magnet_parser import parse_magnet_csv, filter_high_quality_variations
    from keyword_expander import expand_with_magnet_variations

    print("🔄 Keyword Expansion...")

    magnet_keywords = parse_magnet_csv(magnet_csv)
    high_quality = filter_high_quality_variations(magnet_keywords, min_search_volume=max(50, min_search_volume))
    expanded = expand_with_magnet_variations(keywords, high_quality, max_additions=30)
    print()

    return expanded
