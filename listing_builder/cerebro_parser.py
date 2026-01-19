# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/cerebro_parser.py
# Purpose: Parse Helium 10 Cerebro CSV exports for competitor gap analysis
# NOT for: Parsing Data Dive or Magnet CSVs

import csv
from typing import List, Dict, Optional


def parse_cerebro_csv(csv_path: str) -> List[Dict]:
    """
    Parse Helium 10 Cerebro CSV export.

    WHY: Cerebro shows which keywords competitors rank for
    WHY: Gap analysis = find keywords you're missing but competitors have

    Expected columns:
    - Keyword / Search Term
    - Search Volume
    - Cerebro IQ Score (optional)
    - Competing Products (how many ASINs rank)

    Returns:
        List of dicts with: phrase, search_volume, competitors_count
    """
    keywords = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # WHY: Try multiple column name variations (H10 uses different names)
            keyword_col = _find_column(reader.fieldnames, ['Keyword', 'Search Term', 'keyword'])
            volume_col = _find_column(reader.fieldnames, ['Search Volume', 'Volume', 'search volume'])
            competitors_col = _find_column(reader.fieldnames, ['Competing Products', 'Competitors', 'competing products'])

            if not keyword_col or not volume_col:
                print(f"❌ ERROR: Could not find required columns in Cerebro CSV")
                print(f"   Found columns: {reader.fieldnames}")
                return []

            for row in reader:
                try:
                    phrase = row[keyword_col].strip().lower()

                    # WHY: Skip empty or invalid phrases
                    if not phrase or len(phrase) < 3:
                        continue

                    # WHY: Parse search volume (may have commas like "1,234")
                    volume_str = row[volume_col].replace(',', '')
                    search_volume = int(volume_str) if volume_str.isdigit() else 0

                    # WHY: Parse competitors count if available
                    competitors_count = 0
                    if competitors_col and row.get(competitors_col):
                        comp_str = row[competitors_col].replace(',', '')
                        competitors_count = int(comp_str) if comp_str.isdigit() else 0

                    keywords.append({
                        'phrase': phrase,
                        'search_volume': search_volume,
                        'competitors_count': competitors_count
                    })

                except (ValueError, KeyError) as e:
                    continue  # WHY: Skip malformed rows

        print(f"✓ Cerebro: Loaded {len(keywords)} competitor keywords")
        return keywords

    except FileNotFoundError:
        print(f"❌ ERROR: Cerebro CSV not found: {csv_path}")
        return []
    except Exception as e:
        print(f"❌ ERROR: Failed to parse Cerebro CSV: {e}")
        return []


def _find_column(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    """
    Find column name from list of candidates.

    WHY: Helium 10 uses different column names depending on export settings
    WHY: Case-insensitive matching for flexibility
    """
    if not fieldnames:
        return None

    fieldnames_lower = [f.lower() for f in fieldnames]

    for candidate in candidates:
        candidate_lower = candidate.lower()
        for i, field in enumerate(fieldnames_lower):
            if candidate_lower in field or field in candidate_lower:
                return fieldnames[i]

    return None


def filter_high_value_keywords(
    cerebro_keywords: List[Dict],
    min_search_volume: int = 100,
    min_competitors: int = 3
) -> List[Dict]:
    """
    Filter Cerebro keywords for high-value opportunities.

    WHY: Focus on keywords with proven demand (volume) and competition (validation)
    WHY: If ≥3 competitors rank for it, it's a proven keyword

    Args:
        min_search_volume: Minimum monthly searches (default 100)
        min_competitors: Minimum competitors ranking (default 3)
    """
    filtered = []

    for kw in cerebro_keywords:
        # WHY: Skip low-volume keywords (not worth the character budget)
        if kw['search_volume'] < min_search_volume:
            continue

        # WHY: Skip keywords with few competitors (unproven)
        if kw['competitors_count'] > 0 and kw['competitors_count'] < min_competitors:
            continue

        filtered.append(kw)

    # WHY: Sort by search volume descending (highest value first)
    filtered.sort(key=lambda x: x['search_volume'], reverse=True)

    return filtered
