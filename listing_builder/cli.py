#!/usr/bin/env python3
# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/cli.py
# Purpose: Command-line interface for listing optimizer with enhanced CSV options
# NOT for: Business logic or optimization algorithms

"""
CLI Interface
Command-line interface for running Amazon Listing Optimizer with optional enhancements.
"""

import sys
import argparse
from listing_optimizer import optimize_listing
from output import save_listing_to_file


def main():
    """
    CLI entry point with argparse for optional CSV files.

    WHY: Flexible command-line interface with multiple CSV options
    WHY: Supports competitor analysis, variations, and volume filtering
    """
    parser = argparse.ArgumentParser(
        description='Amazon Listing Optimizer with optional enhancements',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (Data Dive only)
  python cli.py data.csv "HAG EXPRESS" "Cutting Board" aggressive

  # With competitor gap analysis
  python cli.py data.csv "Brand" "Product" aggressive --cerebro competitors.csv

  # With keyword variations
  python cli.py data.csv "Brand" "Product" aggressive --magnet variations.csv

  # With search volume filter
  python cli.py data.csv "Brand" "Product" aggressive --min-volume 100

  # Full feature (all options)
  python cli.py data.csv "Brand" "Product" aggressive \\
    --cerebro competitors.csv \\
    --magnet variations.csv \\
    --additional product2.csv product3.csv \\
    --min-volume 100 \\
    --merge-strategy union
        """
    )

    # WHY: Required arguments
    parser.add_argument('csv_path', help='Main Data Dive CSV file (required)')
    parser.add_argument('brand', help='Brand name (e.g., "HAG EXPRESS")')
    parser.add_argument('product_line', help='Product line (e.g., "Cutting Board")')
    parser.add_argument('mode', nargs='?', default='aggressive',
                        choices=['aggressive', 'standard'],
                        help='Optimization mode (default: aggressive)')

    # WHY: Optional CSV enhancements
    parser.add_argument('--cerebro', metavar='CSV',
                        help='Helium 10 Cerebro CSV for competitor gap analysis')
    parser.add_argument('--magnet', metavar='CSV',
                        help='Helium 10 Magnet CSV for keyword variations')
    parser.add_argument('--additional', nargs='+', metavar='CSV',
                        help='Additional Data Dive CSVs to merge')

    # WHY: Optional filters and strategies
    parser.add_argument('--min-volume', type=int, default=0, metavar='N',
                        help='Minimum search volume filter (default: 0 = no filter)')
    parser.add_argument('--merge-strategy', choices=['union', 'intersection'],
                        default='union',
                        help='Strategy for merging multiple Data Dive files (default: union)')

    # WHY: Output options
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='Output file path (default: optimized_listing_BRAND.txt)')

    args = parser.parse_args()

    # WHY: Run optimization with all options
    result = optimize_listing(
        csv_path=args.csv_path,
        brand=args.brand,
        product_line=args.product_line,
        mode=args.mode,
        cerebro_csv=args.cerebro,
        magnet_csv=args.magnet,
        additional_datadive_csvs=args.additional,
        min_search_volume=args.min_volume,
        merge_strategy=args.merge_strategy
    )

    # WHY: Save to file
    output_path = args.output if args.output else f"optimized_listing_{args.brand.replace(' ', '_')}.txt"
    save_listing_to_file(result, output_path)

    print("="*60)
    print("✅ OPTIMIZATION COMPLETE!")
    print("="*60)
    print(f"\nOutput saved to: {output_path}")

    # WHY: Print summary of enhancements used
    if args.cerebro or args.magnet or args.additional or args.min_volume > 0:
        print("\nEnhancements applied:")
        if args.cerebro:
            print(f"  ✓ Competitor gap analysis (Cerebro)")
        if args.magnet:
            print(f"  ✓ Keyword variations (Magnet)")
        if args.additional:
            print(f"  ✓ Merged {len(args.additional)} additional Data Dive files ({args.merge_strategy})")
        if args.min_volume > 0:
            print(f"  ✓ Search volume filter (≥{args.min_volume}/month)")


if __name__ == "__main__":
    main()
