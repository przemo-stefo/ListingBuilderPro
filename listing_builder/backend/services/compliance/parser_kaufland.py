# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/compliance/parser_kaufland.py
# Purpose: Parse Kaufland CSV product data template (semicolon-delimited, UTF-8-BOM, 39 cols)
# NOT for: Validation rules or report generation

import csv
import io
from typing import List, Dict
import structlog

logger = structlog.get_logger()


def parse_kaufland_csv(file_bytes: bytes) -> List[Dict[str, str]]:
    """
    Parse Kaufland product data CSV.

    Format: semicolon delimiter, UTF-8-BOM encoding, ~39 columns.
    Row 1 = headers, Row 2+ = data.

    Returns list of dicts, one per product row.
    Keys are the CSV header names (lowercased, spaces→underscores).
    """
    # Decode with utf-8-sig to strip BOM if present
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Fallback to latin-1 for files saved from Excel with CP1252
        text = file_bytes.decode("latin-1")

    reader = csv.reader(io.StringIO(text), delimiter=";")
    rows = list(reader)

    if len(rows) < 2:
        logger.warning("kaufland_csv_too_short", row_count=len(rows))
        return []

    # Row 0 = headers — normalize to snake_case
    raw_headers = rows[0]
    headers = [_normalize_header(h) for h in raw_headers]

    products = []
    for row_idx, row in enumerate(rows[1:], start=2):
        # Skip completely empty rows
        if not any(cell.strip() for cell in row):
            continue

        product = {"_row_number": row_idx}
        for col_idx, header in enumerate(headers):
            if col_idx < len(row):
                product[header] = row[col_idx].strip()
            else:
                product[header] = ""

        products.append(product)

    logger.info("kaufland_csv_parsed", products=len(products), columns=len(headers))
    return products


def _normalize_header(header: str) -> str:
    """
    Normalize CSV header to a consistent key format.
    'Energy Efficiency Class (2021)' → 'energy_efficiency_class_2021'
    """
    h = header.strip().lower()
    # Replace common separators with underscore
    for char in [" ", "-", "(", ")", "/", "."]:
        h = h.replace(char, "_")
    # Collapse multiple underscores
    while "__" in h:
        h = h.replace("__", "_")
    return h.strip("_")
