#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/listing_optimizer.py
# Purpose: Main orchestrator for listing optimization (ties all modules together)
# NOT for: Individual component tasks (use specific modules instead)

"""
Listing Optimizer - Main Orchestrator
Coordinates all modules to create optimized Amazon listings.
"""

import sys
from pathlib import Path

# WHY: Import all modules
from csv_parser import parse_datadive_csv, get_top_keywords, calculate_coverage_target
from keyword_analyzer import (
    extract_root_words, group_by_relevancy_tier,
    detect_forbidden_keywords, calculate_keyword_score
)
from title_builder import build_aggressive_title, build_standard_title
from backend_optimizer import optimize_backend_keywords
from bullet_generator import generate_bullets
from description_builder import generate_description
from coverage_calculator import (
    calculate_coverage, calculate_section_coverage,
    calculate_exact_match_count
)
from validators import validate_title, validate_bullets, validate_backend, validate_description
from reporting import print_validation_results
from output import save_listing_to_file


def optimize_listing(
    csv_path: str,
    brand: str,
    product_line: str,
    mode: str = 'aggressive',
    cerebro_csv: str = None,
    magnet_csv: str = None,
    additional_datadive_csvs: list = None,
    min_search_volume: int = 0,
    merge_strategy: str = 'union'
) -> dict:
    """
    Main function - optimize complete Amazon listing with optional enhancements.

    WHY: One function to rule them all
    WHY: Takes Data Dive CSV → outputs optimized listing
    WHY: Mode = 'aggressive' (96-98% coverage) or 'standard' (82% coverage)

    Args:
        csv_path: Main Data Dive CSV (required)
        cerebro_csv: Optional Cerebro CSV for competitor gap analysis
        magnet_csv: Optional Magnet CSV for keyword variations
        additional_datadive_csvs: Optional list of additional Data Dive CSVs to merge
        min_search_volume: Minimum search volume filter (0 = no filter)
        merge_strategy: 'union' or 'intersection' for multiple Data Dive files

    Returns dict with:
    - title, bullets, description, backend
    - stats (coverage %, exact matches, etc)
    - validation results
    """
    print(f"\n{'='*60}")
    print(f"AMAZON LISTING OPTIMIZER")
    print(f"{'='*60}\n")

    # STEP 1: Parse Data Dive CSV(s) and apply enhancements
    print("📄 Step 1: Parsing Data Dive CSV(s)...")
    keywords = parse_datadive_csv(csv_path)
    print(f"   ✓ Main CSV: {len(keywords)} keywords")

    # WHY: Process all optional enhancements (extracted to enhancements.py for modularity)
    if cerebro_csv or magnet_csv or additional_datadive_csvs or min_search_volume > 0:
        from enhancements import process_enhancements
        keywords = process_enhancements(
            keywords,
            cerebro_csv=cerebro_csv,
            magnet_csv=magnet_csv,
            additional_datadive_csvs=additional_datadive_csvs,
            min_search_volume=min_search_volume,
            merge_strategy=merge_strategy
        )

    top_200 = get_top_keywords(keywords, 200)
    coverage_targets = calculate_coverage_target(top_200)

    print(f"   ✓ Final keyword count: {len(keywords)}")
    print(f"   ✓ Top 200 keywords extracted")
    print(f"   ✓ Target coverage: {coverage_targets['aggressive_target']} keywords (97%)\n")

    # STEP 2: Analyze keywords
    print("🔍 Step 2: Analyzing keywords...")
    tiers = group_by_relevancy_tier(keywords)
    forbidden = detect_forbidden_keywords(keywords)

    if forbidden:
        print(f"   ⚠️  WARNING: {len(forbidden)} potentially forbidden keywords detected:")
        for kw in forbidden[:5]:
            print(f"      • {kw}")
        print()

    print(f"   ✓ Tier 1 (title): {len(tiers['tier1_title'])} keywords")
    print(f"   ✓ Tier 2 (bullets): {len(tiers['tier2_bullets'])} keywords")
    print(f"   ✓ Tier 3 (backend): {len(tiers['tier3_backend'])} keywords\n")

    # STEP 3: Build title
    print("📝 Step 3: Building title...")

    if mode == 'aggressive':
        title, title_stats = build_aggressive_title(brand, product_line, keywords)
        print(f"   ✓ AGGRESSIVE mode - targeting 7-9 EXACT phrases")
    else:
        title, title_stats = build_standard_title(brand, product_line, keywords)
        print(f"   ✓ STANDARD mode - targeting 3-4 EXACT phrases")

    print(f"   ✓ Length: {title_stats['length']} chars ({title_stats['utilization']:.1f}% utilization)")
    print(f"   ✓ EXACT phrases: {title_stats['exact_phrases']}")
    print(f"   ✓ Title: {title}\n")

    # STEP 4: Generate bullets
    print("🔹 Step 4: Generating bullets...")
    bullets, bullet_stats = generate_bullets(keywords, title)

    print(f"   ✓ {bullet_stats['bullet_count']} bullets generated")
    print(f"   ✓ Avg length: {bullet_stats['avg_length']} chars")
    print(f"   ✓ Keywords covered: {bullet_stats['keywords_covered']}\n")

    # STEP 5: Generate description
    print("📄 Step 5: Generating description...")
    description = generate_description(keywords, title, bullets, brand, product_line)
    desc_validation = validate_description(description)

    print(f"   ✓ Length: {desc_validation['char_count']} chars ({desc_validation['utilization']:.1f}% utilization)\n")

    # STEP 6: Optimize backend
    print("🔧 Step 6: Optimizing backend keywords...")
    backend, backend_stats = optimize_backend_keywords(keywords, title, bullets)

    print(f"   ✓ Bytes: {backend_stats['byte_size']}/250 ({backend_stats['utilization']:.1f}% utilization)")
    print(f"   ✓ Keywords packed: {backend_stats['keyword_count']}")
    print(f"   ✓ Unique words: {backend_stats['unique_words']}\n")

    # STEP 7: Calculate coverage
    print("📊 Step 7: Calculating coverage...")
    coverage = calculate_coverage(keywords, title, bullets, description, backend)
    section_cov = calculate_section_coverage(keywords, title, bullets, backend)
    exact_matches = calculate_exact_match_count(keywords, title)

    print(f"   ✓ Overall coverage: {coverage['coverage_pct']}%")
    print(f"   ✓ Mode: {coverage['mode']}")
    print(f"   ✓ EXACT matches in title: {exact_matches}")
    print(f"   ✓ Title coverage: {section_cov['title_coverage']}%")
    print(f"   ✓ Bullets coverage: {section_cov['bullets_coverage']}%")
    print(f"   ✓ Backend coverage: {section_cov['backend_coverage']}%\n")

    # STEP 8: Validation
    print("✅ Step 8: Validating listing...")
    title_validation = validate_title(title)
    bullet_validation = validate_bullets(bullets)
    backend_validation = validate_backend(backend)

    # WHY: Use reporting function to print validation (extracted for modularity)
    all_valid = print_validation_results(title_validation, bullet_validation, backend_validation, desc_validation)

    # WHY: Return complete listing data
    return {
        'listing': {
            'title': title,
            'bullets': bullets,
            'description': description,
            'backend': backend
        },
        'stats': {
            'coverage_pct': coverage['coverage_pct'],
            'mode': coverage['mode'],
            'exact_matches': exact_matches,
            'title_stats': title_stats,
            'bullet_stats': bullet_stats,
            'backend_stats': backend_stats,
            'section_coverage': section_cov
        },
        'validation': {
            'all_valid': all_valid,
            'title': title_validation,
            'bullets': bullet_validation,
            'backend': backend_validation,
            'description': desc_validation
        },
        'keywords': {
            'total': len(keywords),
            'top_200': top_200,
            'tiers': tiers,
            'forbidden': forbidden
        }
    }


