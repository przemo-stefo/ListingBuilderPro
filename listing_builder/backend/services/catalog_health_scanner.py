# backend/services/catalog_health_scanner.py
# Purpose: 3-phase catalog scan pipeline (reports → inspection → analysis)
# NOT for: Query/fix operations (catalog_health_service.py) or API routes

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.catalog_health import CatalogScan, CatalogIssue
from services.sp_api_catalog import MARKETPLACE_IDS
from services.sp_api_reports import fetch_report_pipeline
from services.sp_api_listings import search_listings_items

logger = structlog.get_logger()

# WHY severity mapping: SP-API issue severity → our severity levels
SEVERITY_MAP = {
    "ERROR": "critical",
    "WARNING": "warning",
    "INFO": "info",
}

# WHY category mapping: SP-API issue categories → our issue types
CATEGORY_TO_TYPE = {
    "MISSING_ATTRIBUTE": "missing_attribute",
    "INVALID_IMAGE": "low_quality_image",
    "INVALID_PRICE": "invalid_price",
    "LISTING_SUPPRESSED": "suppressed_listing",
    "SEARCH_SUPPRESSED": "suppressed_listing",
}


async def run_scan(scan_id: str, db: Session) -> None:
    """Execute the 3-phase scan pipeline.

    WHY separate from start_scan: Runs as background task
    with its own DB session (request may have ended).
    """
    scan = db.query(CatalogScan).filter(CatalogScan.id == scan_id).first()
    if not scan:
        logger.error("catalog_health_scan_not_found", scan_id=scan_id)
        return

    scan.status = "scanning"
    scan.started_at = datetime.now(timezone.utc)
    scan.progress = {"phase": "reports", "percent": 5}
    db.commit()

    try:
        await _phase1_bulk_reports(scan, db)
        await _phase2_deep_inspection(scan, db)
        await _phase3_dedup(scan, db)

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.issues_found = db.query(CatalogIssue).filter(CatalogIssue.scan_id == scan.id).count()
        scan.progress = {"phase": "done", "percent": 100}
        db.commit()
        logger.info("catalog_health_scan_done", scan_id=scan_id, issues=scan.issues_found)

    except Exception as e:
        scan.status = "failed"
        scan.error_message = "Scan failed — check logs for details"
        scan.progress = {"phase": "error", "percent": 0}
        db.commit()
        logger.error("catalog_health_scan_error", scan_id=scan_id, error=str(e)[:200])


async def _phase1_bulk_reports(scan: CatalogScan, db: Session) -> None:
    """Phase 1: Fetch 3 bulk reports in parallel.

    WHY asyncio.gather: FYP, stranded, and full catalog are independent API calls.
    WHY reports first: One API call gives full catalog snapshot vs N per-item calls.
    """
    marketplace_ids = [MARKETPLACE_IDS.get(scan.marketplace, MARKETPLACE_IDS["DE"])]
    scan.progress = {"phase": "reports", "percent": 10, "detail": "Fetching reports..."}
    db.commit()

    fyp_rows, stranded_rows, all_rows = await asyncio.gather(
        fetch_report_pipeline("GET_MERCHANTS_LISTINGS_FYP_REPORT", marketplace_ids, user_id=scan.user_id, db=db),
        fetch_report_pipeline("GET_STRANDED_INVENTORY_UI_DATA", marketplace_ids, user_id=scan.user_id, db=db),
        fetch_report_pipeline("GET_MERCHANT_LISTINGS_ALL_DATA", marketplace_ids, user_id=scan.user_id, db=db),
    )

    _ingest_fyp(scan, fyp_rows, db)
    _ingest_stranded(scan, stranded_rows, db)

    if all_rows:
        scan.total_listings = len(all_rows)
        # WHY store SKUs: Phase 2 uses them for broken-variation detection
        skus = [r.get("seller-sku", "") or r.get("SKU", "") for r in all_rows if r.get("seller-sku") or r.get("SKU")]
        scan.scan_data = {"skus": skus[:2000]}

    scan.progress = {"phase": "reports", "percent": 45, "detail": "Reports complete"}
    db.commit()


def _ingest_fyp(scan: CatalogScan, rows: Optional[List[Dict]], db: Session) -> None:
    """Create suppressed_listing issues from FYP report."""
    if not rows:
        return
    for row in rows:
        reason = row.get("Status Change Reason", "") or row.get("status-change-reason", "")
        if not reason:
            continue
        sku = row.get("SKU", "") or row.get("seller-sku", "")
        asin = row.get("ASIN", "") or row.get("asin", "")
        condition = row.get("Condition", "") or row.get("condition", "")
        db.add(CatalogIssue(
            scan_id=scan.id, asin=asin, sku=sku,
            issue_type="suppressed_listing", severity="critical",
            title=f"Listing suppressed: {sku}",
            description=f"Reason: {reason}. Condition: {condition}",
            amazon_issue_code=reason[:100] if reason else None,
        ))


def _ingest_stranded(scan: CatalogScan, rows: Optional[List[Dict]], db: Session) -> None:
    """Create stranded_inventory issues from stranded report."""
    if not rows:
        return
    for row in rows:
        sku = row.get("sku", "") or row.get("SKU", "")
        if not sku:
            continue
        asin = row.get("asin", "") or row.get("ASIN", "")
        reason = row.get("stranded-reason", "") or row.get("Stranded Reason", "")
        qty = row.get("afn-fulfillable-quantity", "0")
        db.add(CatalogIssue(
            scan_id=scan.id, asin=asin, sku=sku,
            issue_type="stranded_inventory", severity="critical",
            title=f"Stranded inventory: {sku} ({qty} units)",
            description=f"FBA inventory without active listing. Reason: {reason}",
            amazon_issue_code=reason[:100] if reason else None,
        ))


async def _phase2_deep_inspection(scan: CatalogScan, db: Session) -> None:
    """Phase 2: Per-item Listings API inspection for issues + broken variations."""
    if not scan.seller_id:
        scan.progress = {"phase": "inspection", "percent": 60, "detail": "No seller_id — skipping"}
        db.commit()
        return

    scan.progress = {"phase": "inspection", "percent": 50, "detail": "Inspecting listings..."}
    db.commit()

    result = await search_listings_items(
        seller_id=scan.seller_id, marketplace=scan.marketplace,
        db=db, user_id=scan.user_id,
    )
    if "error" in result:
        logger.warning("catalog_health_phase2_error", error=result["error"])
        scan.progress = {"phase": "inspection", "percent": 70, "detail": f"Search error: {result['error'][:50]}"}
        db.commit()
        return

    items = result.get("items", [])
    # WHY scan_data SKUs: Full catalog from Phase 1, not issue-table SKUs — prevents false positives
    catalog_skus = set(scan.scan_data.get("skus", [])) if scan.scan_data else set()

    for i, item in enumerate(items):
        _inspect_item(scan, item, catalog_skus, db)
        if i > 0 and i % 50 == 0:
            pct = 50 + int((i / max(len(items), 1)) * 30)
            scan.progress = {"phase": "inspection", "percent": min(pct, 80), "detail": f"Inspected {i}/{len(items)}"}
            db.commit()
    db.commit()


def _inspect_item(scan: CatalogScan, item: Dict, catalog_skus: set, db: Session) -> None:
    """Inspect one listing: SP-API issues + broken variation check."""
    sku = item.get("sku", "")
    summaries = item.get("summaries", [{}])
    asin = summaries[0].get("asin", "") if summaries else ""

    for issue_data in item.get("issues", []):
        categories = issue_data.get("categories", [])
        issue_type = next((CATEGORY_TO_TYPE[c] for c in categories if c in CATEGORY_TO_TYPE), "missing_attribute")
        db.add(CatalogIssue(
            scan_id=scan.id, asin=asin, sku=sku,
            issue_type=issue_type,
            severity=SEVERITY_MAP.get(issue_data.get("severity", "WARNING"), "warning"),
            title=f"{issue_type.replace('_', ' ').title()}: {sku}",
            description=(issue_data.get("message", "") or "")[:500] or None,
            amazon_issue_code=(issue_data.get("code", "") or "")[:100] or None,
            fix_proposal=_generate_fix_proposal(issue_type, sku, issue_data),
        ))

    for rel in item.get("attributes", {}).get("child_parent_sku_relationship", []):
        parent_sku = rel.get("value", {}).get("parent_sku", "") if isinstance(rel.get("value"), dict) else ""
        if parent_sku and parent_sku not in catalog_skus:
            db.add(CatalogIssue(
                scan_id=scan.id, asin=asin, sku=sku,
                issue_type="broken_variation", severity="critical",
                title=f"Broken variation: {sku} → parent {parent_sku} not found",
                description=f"Child SKU references parent '{parent_sku}' which doesn't exist in catalog",
            ))


async def _phase3_dedup(scan: CatalogScan, db: Session) -> None:
    """Phase 3: SQL-based deduplication.

    WHY SQL not Python: Avoids loading all issues into memory.
    Keeps the most actionable record per (sku, issue_type).
    """
    scan.progress = {"phase": "analysis", "percent": 85, "detail": "Deduplicating issues..."}
    db.commit()

    # WHY window function: Rank duplicates by actionability, delete losers in one query
    # WHY sku IS NOT NULL: NULL SKUs can't be meaningfully deduped
    dedup_sql = text("""
        DELETE FROM catalog_issues
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY sku, issue_type
                    ORDER BY
                        CASE WHEN fix_proposal IS NOT NULL THEN 0 ELSE 1 END,
                        CASE WHEN amazon_issue_code IS NOT NULL THEN 0 ELSE 1 END,
                        created_at DESC
                ) AS rn
                FROM catalog_issues
                WHERE scan_id = :scan_id AND sku IS NOT NULL
            ) ranked WHERE rn > 1
        )
    """)
    result = db.execute(dedup_sql, {"scan_id": scan.id})
    if result.rowcount:
        logger.info("catalog_health_deduped", scan_id=scan.id, removed=result.rowcount)
    db.commit()

    scan.progress = {"phase": "analysis", "percent": 95, "detail": "Finalizing..."}
    db.commit()


def _generate_fix_proposal(issue_type: str, sku: str, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate fix proposal for missing_attribute issues only."""
    if issue_type != "missing_attribute":
        return None
    attr_names = issue_data.get("attributeNames", [])
    if not attr_names:
        return None
    patches = [{"op": "replace", "path": f"/attributes/{attr}", "value": []} for attr in attr_names]
    return {"action": "patch", "sku": sku, "patches": patches, "note": "Placeholder values — review before applying"}
