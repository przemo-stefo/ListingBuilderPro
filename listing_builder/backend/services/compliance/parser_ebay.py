# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/compliance/parser_ebay.py
# Purpose: Parse eBay bulk listing XLSX template (Row 4 = headers, 81+ cols)
# NOT for: Validation rules or report generation

from typing import List, Dict
import structlog

logger = structlog.get_logger()

# WHY openpyxl import is inside the function:
# Keeps module importable even if openpyxl not installed yet,
# and avoids loading the heavy lib at startup when not needed.


def parse_ebay_xlsx(file_bytes: bytes) -> List[Dict[str, str]]:
    """
    Parse eBay bulk listing XLSX.

    Format: Row 1-3 = eBay metadata/instructions, Row 4 = column headers, Row 5+ = data.
    Columns matched by header name (not position) so it's robust against reordering.

    Returns list of dicts, one per product row.
    Keys are the original eBay header names (as-is, no normalization — rules reference them directly).
    """
    import openpyxl

    from io import BytesIO
    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 5:
        logger.warning("ebay_xlsx_too_short", row_count=len(rows))
        return []

    # Row 4 (index 3) = headers
    raw_headers = rows[3]
    headers = [str(h).strip() if h is not None else "" for h in raw_headers]

    products = []
    for row_idx, row in enumerate(rows[4:], start=5):
        # Skip empty rows
        if not any(cell is not None and str(cell).strip() for cell in row):
            continue

        product = {"_row_number": row_idx}
        for col_idx, header in enumerate(headers):
            if not header:
                continue
            val = row[col_idx] if col_idx < len(row) else None
            product[header] = str(val).strip() if val is not None else ""

        products.append(product)

    logger.info("ebay_xlsx_parsed", products=len(products), columns=len(headers))
    return products
