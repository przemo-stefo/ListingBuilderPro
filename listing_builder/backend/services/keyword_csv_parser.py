# backend/services/keyword_csv_parser.py
# Purpose: Parse Helium10 (Cerebro/Magnet/BlackBox) and DataDive CSV exports via upload
# NOT for: Reading files from disk (old parsers did that — this works with uploaded content)

from __future__ import annotations

import csv
import io
import re
from typing import List, Dict, Any, Optional

import structlog

logger = structlog.get_logger()

# WHY: Column name variations across tools. Helium10 changes names between versions.
_KEYWORD_COLS = ["keyword", "search term", "phrase", "magnet iq score"]
_VOLUME_COLS = ["search volume", "volume", "exact volume", "search vol."]
_RELEVANCY_COLS = ["relevancy", "relevance", "rel.", "relevance score"]
_RJ_COLS = ["ranking juice", "ranking juice ®", "rj", "ranking juice score"]
_COMPETITION_COLS = ["competition", "competing products", "competitors", "comp."]
_SMART_SCORE_COLS = ["smart score", "iq score", "cerebro iq score", "magnet iq"]
_INDEX_COLS = ["my_listing", "my listing", "indexed", "index status"]

# WHY: BlackBox product columns (for competitor research, not keyword import)
_ASIN_COLS = ["asin"]
_REVENUE_COLS = ["monthly revenue", "revenue", "est. monthly revenue", "estimated revenue"]
_BSR_COLS = ["bsr", "best seller rank", "best sellers rank", "rank"]
_PRICE_COLS = ["price", "product price", "current price"]
_REVIEWS_COLS = ["reviews", "review count", "# reviews"]


def parse_keyword_csv(content: str) -> Dict[str, Any]:
    """Parse CSV content from Helium10 or DataDive upload.

    WHY: Unified parser for all keyword CSV formats. Auto-detects tool by column names.
    Returns keywords with search_volume, relevancy, ranking_juice — ready for optimizer.

    Args:
        content: Raw CSV text (from file upload)

    Returns:
        {
            "source": "datadive" | "cerebro" | "magnet" | "blackbox" | "generic",
            "keywords": [{phrase, search_volume, relevancy, ranking_juice, competition, ...}],
            "stats": {total, with_volume, avg_volume, top_keyword},
            "error": None | str
        }
    """
    if not content or not content.strip():
        return {"source": "unknown", "keywords": [], "stats": {}, "error": "Empty CSV content"}

    try:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return {"source": "unknown", "keywords": [], "stats": {}, "error": "No columns found in CSV"}

        source = _detect_source(reader.fieldnames)
        keyword_col = _find_col(reader.fieldnames, _KEYWORD_COLS)
        volume_col = _find_col(reader.fieldnames, _VOLUME_COLS)

        # WHY: BlackBox = product research (ASINs), not keywords — different output
        if source == "blackbox":
            return _parse_blackbox(reader)

        if not keyword_col:
            return {
                "source": source, "keywords": [], "stats": {},
                "error": f"No keyword column found. Columns: {', '.join(reader.fieldnames)}",
            }

        # Optional columns
        relevancy_col = _find_col(reader.fieldnames, _RELEVANCY_COLS)
        rj_col = _find_col(reader.fieldnames, _RJ_COLS)
        competition_col = _find_col(reader.fieldnames, _COMPETITION_COLS)
        smart_score_col = _find_col(reader.fieldnames, _SMART_SCORE_COLS)
        index_col = _find_col(reader.fieldnames, _INDEX_COLS)

        keywords: List[Dict[str, Any]] = []
        seen: set = set()

        for row in reader:
            phrase = (row.get(keyword_col) or "").strip().lower()

            # WHY: Skip empty, too short, or combined phrases (DataDive artifacts)
            if not phrase or len(phrase) < 2:
                continue
            if any(c in phrase for c in ["|", "&"]) and "," not in phrase:
                continue
            if phrase in seen:
                continue
            seen.add(phrase)

            sv = _parse_int(row.get(volume_col, "0"))
            rel = _parse_float(row.get(relevancy_col, "0")) if relevancy_col else 0.0
            rj = _parse_int(row.get(rj_col, "0")) if rj_col else 0
            comp = _parse_float(row.get(competition_col, "0")) if competition_col else 0.0
            smart = _parse_float(row.get(smart_score_col, "0")) if smart_score_col else 0.0
            indexed = (row.get(index_col, "NONE").strip().upper() != "NONE") if index_col else False

            # WHY: Calculate RJ if not provided (Cerebro/Magnet don't have it)
            if rj == 0 and sv > 0:
                # WHY: Approximate DataDive RJ formula for tools that don't provide it
                rel_factor = max(rel, 0.5)  # Default 0.5 if no relevancy data
                comp_factor = 0.5 + 0.5 * (1.0 - min(comp, 1.0))
                word_count = len(phrase.split())
                length_boost = 1.1 if 2 <= word_count <= 3 else (1.05 if word_count > 3 else 1.0)
                rj = int(sv * (0.5 + 0.5 * rel_factor) * comp_factor * length_boost)

            # WHY: Estimate relevancy from smart score if we have Magnet data
            if rel == 0 and smart > 0:
                rel = round(smart / 10.0, 2)  # Smart Score 0-10 → Relevancy 0-1.0

            keywords.append({
                "phrase": phrase,
                "search_volume": sv,
                "relevancy": rel,
                "ranking_juice": rj,
                "competition": comp,
                "smart_score": smart,
                "indexed": indexed,
                "word_count": len(phrase.split()),
            })

        # WHY: Sort by ranking_juice DESC (same as DataDive), fallback search_volume
        keywords.sort(key=lambda k: (k["ranking_juice"], k["search_volume"]), reverse=True)

        stats = _calc_stats(keywords)
        logger.info("keyword_csv_parsed", source=source, total=len(keywords), with_volume=stats.get("with_volume", 0))

        return {"source": source, "keywords": keywords, "stats": stats, "error": None}

    except Exception as e:
        logger.error("keyword_csv_parse_error", error=str(e))
        return {"source": "unknown", "keywords": [], "stats": {}, "error": str(e)}


def _detect_source(fieldnames: List[str]) -> str:
    """Detect CSV source tool from column names."""
    lower = [f.lower() for f in fieldnames]
    joined = " ".join(lower)

    if "ranking juice" in joined or "my_listing" in joined:
        return "datadive"
    if "cerebro" in joined:
        return "cerebro"
    if "magnet" in joined:
        return "magnet"
    # WHY: BlackBox has ASIN + Revenue columns, not keyword columns
    if any("asin" in c for c in lower) and any("revenue" in c for c in lower):
        return "blackbox"
    if any("smart score" in c for c in lower):
        return "magnet"
    if any("competing products" in c for c in lower):
        return "cerebro"
    return "generic"


def _parse_blackbox(reader: csv.DictReader) -> Dict[str, Any]:
    """Parse BlackBox CSV — returns competitor products, not keywords."""
    asin_col = _find_col(reader.fieldnames, _ASIN_COLS)
    revenue_col = _find_col(reader.fieldnames, _REVENUE_COLS)
    bsr_col = _find_col(reader.fieldnames, _BSR_COLS)
    price_col = _find_col(reader.fieldnames, _PRICE_COLS)
    reviews_col = _find_col(reader.fieldnames, _REVIEWS_COLS)

    products = []
    for row in reader:
        asin = (row.get(asin_col, "") if asin_col else "").strip()
        if not asin:
            continue
        products.append({
            "asin": asin,
            "title": row.get("Title", row.get("Product Title", "")),
            "monthly_revenue": _parse_currency(row.get(revenue_col, "0")) if revenue_col else 0,
            "bsr_rank": _parse_int(row.get(bsr_col, "999999")) if bsr_col else 999999,
            "price": _parse_currency(row.get(price_col, "0")) if price_col else 0,
            "review_count": _parse_int(row.get(reviews_col, "0")) if reviews_col else 0,
        })

    return {
        "source": "blackbox",
        "keywords": [],
        "products": products,
        "stats": {"total_products": len(products)},
        "error": None,
    }


def _find_col(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    """Find column by fuzzy matching candidate names (case-insensitive substring)."""
    if not fieldnames:
        return None
    lower_fields = [(f.lower().strip(), f) for f in fieldnames]
    for candidate in candidates:
        c = candidate.lower()
        for lower_f, original_f in lower_fields:
            if c in lower_f or lower_f in c:
                return original_f
    return None


def _parse_int(s: str) -> int:
    """Parse integer from string, stripping commas/currency/spaces."""
    s = re.sub(r"[,$€£\s#]", "", s.strip())
    if " in " in s:
        s = s.split(" in ")[0]
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _parse_float(s: str) -> float:
    """Parse float, handling comma as decimal separator (EU format)."""
    s = s.strip().replace(",", ".")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_currency(s: str) -> float:
    """Parse currency value (e.g., '$1,234.56' → 1234.56)."""
    s = re.sub(r"[,$€£\s]", "", s.strip())
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _calc_stats(keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for parsed keywords."""
    if not keywords:
        return {"total": 0, "with_volume": 0, "avg_volume": 0, "top_keyword": ""}

    with_vol = [k for k in keywords if k["search_volume"] > 0]
    return {
        "total": len(keywords),
        "with_volume": len(with_vol),
        "avg_volume": int(sum(k["search_volume"] for k in with_vol) / len(with_vol)) if with_vol else 0,
        "top_keyword": keywords[0]["phrase"] if keywords else "",
        "top_rj": keywords[0]["ranking_juice"] if keywords else 0,
    }
