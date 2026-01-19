# /Users/shawn/Projects/Amazon/amazon-master-tool/listing_builder/magnet_parser.py
# Purpose: Parse Helium 10 Magnet CSV exports for keyword variations/synonyms
# NOT for: Parsing Data Dive or Cerebro CSVs

import csv
from typing import List, Dict, Optional


def parse_magnet_csv(csv_path: str) -> List[Dict]:
    """
    Parse Helium 10 Magnet CSV export.

    WHY: Magnet finds keyword variations and related terms
    WHY: Expands beyond Data Dive's exact matches

    Expected columns:
    - Keyword / Magnet IQ Score / Search Term
    - Search Volume
    - Smart Score (optional)
    - Competing Products (optional)

    Returns:
        List of dicts with: phrase, search_volume, smart_score
    """
    keywords = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # WHY: Try multiple column name variations
            keyword_col = _find_column(reader.fieldnames, ['Keyword', 'Search Term', 'Magnet IQ Score'])
            volume_col = _find_column(reader.fieldnames, ['Search Volume', 'Volume', 'search volume'])
            score_col = _find_column(reader.fieldnames, ['Smart Score', 'Magnet IQ Score', 'IQ Score'])

            if not keyword_col or not volume_col:
                print(f"❌ ERROR: Could not find required columns in Magnet CSV")
                print(f"   Found columns: {reader.fieldnames}")
                return []

            for row in reader:
                try:
                    phrase = row[keyword_col].strip().lower()

                    # WHY: Skip empty or invalid phrases
                    if not phrase or len(phrase) < 3:
                        continue

                    # WHY: Parse search volume
                    volume_str = row[volume_col].replace(',', '')
                    search_volume = int(volume_str) if volume_str.isdigit() else 0

                    # WHY: Parse smart score if available (0-10 scale)
                    smart_score = 0
                    if score_col and row.get(score_col):
                        try:
                            smart_score = float(row[score_col])
                        except ValueError:
                            smart_score = 0

                    keywords.append({
                        'phrase': phrase,
                        'search_volume': search_volume,
                        'smart_score': smart_score
                    })

                except (ValueError, KeyError) as e:
                    continue  # WHY: Skip malformed rows

        print(f"✓ Magnet: Loaded {len(keywords)} keyword variations")
        return keywords

    except FileNotFoundError:
        print(f"❌ ERROR: Magnet CSV not found: {csv_path}")
        return []
    except Exception as e:
        print(f"❌ ERROR: Failed to parse Magnet CSV: {e}")
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


def filter_high_quality_variations(
    magnet_keywords: List[Dict],
    min_search_volume: int = 50,
    min_smart_score: float = 5.0
) -> List[Dict]:
    """
    Filter Magnet keywords for high-quality variations.

    WHY: Magnet returns MANY variations (100s), need to filter noise
    WHY: Smart Score ≥5 = decent relevancy + volume balance

    Args:
        min_search_volume: Minimum monthly searches (default 50, lower than Cerebro)
        min_smart_score: Minimum H10 Smart Score (default 5.0)
    """
    filtered = []

    for kw in magnet_keywords:
        # WHY: Skip very low volume (but lower threshold than Cerebro)
        if kw['search_volume'] < min_search_volume:
            continue

        # WHY: Skip low-quality variations if smart score available
        if kw['smart_score'] > 0 and kw['smart_score'] < min_smart_score:
            continue

        filtered.append(kw)

    # WHY: Sort by search volume descending
    filtered.sort(key=lambda x: x['search_volume'], reverse=True)

    return filtered
