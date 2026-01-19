#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/output.py
# Purpose: Output formatting and file saving functions
# NOT for: Business logic or calculations

"""
Output Formatter
Saves optimized listings to text files in copy-paste ready format.
"""


def save_listing_to_file(result: dict, output_path: str):
    """
    Save optimized listing to text file.

    WHY: Easy review and copy-paste to Amazon Seller Central
    WHY: Formatted for readability
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        listing = result['listing']
        stats = result['stats']

        f.write("="*60 + "\n")
        f.write("OPTIMIZED AMAZON LISTING\n")
        f.write("="*60 + "\n\n")

        f.write(f"COVERAGE: {stats['coverage_pct']}% ({stats['mode']} MODE)\n")
        f.write(f"EXACT MATCHES: {stats['exact_matches']}\n\n")

        f.write("="*60 + "\n")
        f.write("TITLE\n")
        f.write("="*60 + "\n")
        f.write(listing['title'] + "\n\n")

        f.write("="*60 + "\n")
        f.write("BULLET POINTS\n")
        f.write("="*60 + "\n")
        for i, bullet in enumerate(listing['bullets'], 1):
            f.write(f"{i}. {bullet}\n\n")

        f.write("="*60 + "\n")
        f.write("DESCRIPTION\n")
        f.write("="*60 + "\n")
        f.write(listing['description'] + "\n\n")

        f.write("="*60 + "\n")
        f.write("BACKEND SEARCH TERMS\n")
        f.write("="*60 + "\n")
        f.write(listing['backend'] + "\n\n")

        f.write("="*60 + "\n")
        f.write("STATISTICS\n")
        f.write("="*60 + "\n")
        f.write(f"Title: {stats['title_stats']['length']} chars, {stats['title_stats']['utilization']:.1f}%\n")
        f.write(f"Bullets: {stats['bullet_stats']['bullet_count']} bullets, avg {stats['bullet_stats']['avg_length']} chars\n")
        f.write(f"Backend: {stats['backend_stats']['byte_size']} bytes, {stats['backend_stats']['utilization']:.1f}%\n")
        f.write(f"\nSection Coverage:\n")
        f.write(f"  Title: {stats['section_coverage']['title_coverage']}%\n")
        f.write(f"  Bullets: {stats['section_coverage']['bullets_coverage']}%\n")
        f.write(f"  Backend: {stats['section_coverage']['backend_coverage']}%\n")

    print(f"✅ Listing saved to: {output_path}\n")
