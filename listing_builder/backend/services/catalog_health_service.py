# backend/services/catalog_health_service.py
# Purpose: Catalog Health Check scan logic — 3-phase pipeline
# NOT for: API routes (catalog_health_routes.py) or SP-API communication (sp_api_*)

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy.orm import Session

from models.catalog_health import CatalogScan, CatalogIssue
from models.oauth_connection import OAuthConnection
from services.sp_api_auth import credentials_configured
from services.sp_api_catalog import MARKETPLACE_IDS
from services.sp_api_reports import fetch_report_pipeline
from services.sp_api_listings import get_listing, patch_listing, search_listings_items

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


async def start_scan(
    user_id: str, marketplace: str, db: Session
) -> CatalogScan:
    """Create a new scan record in pending state."""
    connection = _get_seller_connection(user_id, marketplace, db)
    seller_id = connection.seller_id if connection else None

    scan = CatalogScan(
        user_id=user_id,
        marketplace=marketplace.upper(),
        seller_id=seller_id,
        status="pending",
        progress={"phase": "waiting", "percent": 0},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


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
        # Phase 1: Bulk reports
        await _phase1_bulk_reports(scan, db)

        # Phase 2: Deep inspection via Listings API
        await _phase2_deep_inspection(scan, db)

        # Phase 3: Cross-reference analysis + deduplication
        await _phase3_analysis(scan, db)

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.issues_found = db.query(CatalogIssue).filter(CatalogIssue.scan_id == scan.id).count()
        scan.progress = {"phase": "done", "percent": 100}
        db.commit()

        logger.info("catalog_health_scan_done", scan_id=scan_id, issues=scan.issues_found)

    except Exception as e:
        scan.status = "failed"
        scan.error_message = str(e)[:500]
        scan.progress = {"phase": "error", "percent": 0}
        db.commit()
        logger.error("catalog_health_scan_error", scan_id=scan_id, error=str(e)[:200])


async def _phase1_bulk_reports(scan: CatalogScan, db: Session) -> None:
    """Phase 1: Fetch bulk reports for suppressed listings and stranded inventory.

    WHY reports first: One API call gives full catalog snapshot vs N per-item calls.
    """
    marketplace_id = MARKETPLACE_IDS.get(scan.marketplace, MARKETPLACE_IDS["DE"])
    marketplace_ids = [marketplace_id]

    scan.progress = {"phase": "reports", "percent": 10, "detail": "Fetching FYP report..."}
    db.commit()

    # FYP report — suppressed listings with reasons
    fyp_rows = await fetch_report_pipeline(
        "GET_MERCHANTS_LISTINGS_FYP_REPORT",
        marketplace_ids,
        user_id=scan.user_id,
        db=db,
    )
    if fyp_rows:
        for row in fyp_rows:
            condition = row.get("Condition", "") or row.get("condition", "")
            sku = row.get("SKU", "") or row.get("seller-sku", "")
            asin = row.get("ASIN", "") or row.get("asin", "")
            reason = row.get("Status Change Reason", "") or row.get("status-change-reason", "")

            if reason:  # Only suppressed listings have a reason
                issue = CatalogIssue(
                    scan_id=scan.id,
                    asin=asin,
                    sku=sku,
                    issue_type="suppressed_listing",
                    severity="critical",
                    title=f"Listing suppressed: {sku}",
                    description=f"Reason: {reason}. Condition: {condition}",
                    amazon_issue_code=reason[:100] if reason else None,
                )
                db.add(issue)

    scan.progress = {"phase": "reports", "percent": 30, "detail": "Fetching stranded inventory..."}
    db.commit()

    # Stranded inventory report
    stranded_rows = await fetch_report_pipeline(
        "GET_STRANDED_INVENTORY_UI_DATA",
        marketplace_ids,
        user_id=scan.user_id,
        db=db,
    )
    if stranded_rows:
        for row in stranded_rows:
            sku = row.get("sku", "") or row.get("SKU", "")
            asin = row.get("asin", "") or row.get("ASIN", "")
            reason = row.get("stranded-reason", "") or row.get("Stranded Reason", "")
            qty = row.get("afn-fulfillable-quantity", "0")

            if sku:
                issue = CatalogIssue(
                    scan_id=scan.id,
                    asin=asin,
                    sku=sku,
                    issue_type="stranded_inventory",
                    severity="critical",
                    title=f"Stranded inventory: {sku} ({qty} units)",
                    description=f"FBA inventory without active listing. Reason: {reason}",
                    amazon_issue_code=reason[:100] if reason else None,
                )
                db.add(issue)

    scan.progress = {"phase": "reports", "percent": 45, "detail": "Fetching full catalog..."}
    db.commit()

    # Full catalog — count total listings
    all_rows = await fetch_report_pipeline(
        "GET_MERCHANT_LISTINGS_ALL_DATA",
        marketplace_ids,
        user_id=scan.user_id,
        db=db,
    )
    if all_rows:
        scan.total_listings = len(all_rows)
        # WHY store SKUs: Phase 2 needs them for per-item inspection
        skus = [r.get("seller-sku", "") or r.get("SKU", "") for r in all_rows if r.get("seller-sku") or r.get("SKU")]
        scan.scan_data = {"skus": skus[:2000]}  # Cap at 2000 to avoid JSONB bloat

    db.commit()


async def _phase2_deep_inspection(scan: CatalogScan, db: Session) -> None:
    """Phase 2: Per-item Listings API inspection for issues.

    WHY per-item: Reports don't include detailed issue codes or variation data.
    Listings API issues array gives specific, actionable error codes.
    """
    if not scan.seller_id:
        scan.progress = {"phase": "inspection", "percent": 60, "detail": "No seller_id — skipping deep inspection"}
        db.commit()
        return

    scan.progress = {"phase": "inspection", "percent": 50, "detail": "Inspecting listings..."}
    db.commit()

    # Use searchListingsItems for batch inspection
    result = await search_listings_items(
        seller_id=scan.seller_id,
        marketplace=scan.marketplace,
        db=db,
        user_id=scan.user_id,
    )

    if "error" in result:
        logger.warning("catalog_health_phase2_error", error=result["error"])
        scan.progress = {"phase": "inspection", "percent": 70, "detail": f"Search error: {result['error'][:50]}"}
        db.commit()
        return

    items = result.get("items", [])
    existing_skus = {i.sku for i in db.query(CatalogIssue.sku).filter(CatalogIssue.scan_id == scan.id).all() if i.sku}

    for i, item in enumerate(items):
        sku = item.get("sku", "")
        summaries = item.get("summaries", [{}])
        asin = summaries[0].get("asin", "") if summaries else ""
        issues = item.get("issues", [])

        for issue_data in issues:
            severity_str = issue_data.get("severity", "WARNING")
            categories = issue_data.get("categories", [])
            message = issue_data.get("message", "")
            code = issue_data.get("code", "")

            # Map SP-API categories to our issue types
            issue_type = "missing_attribute"  # default
            for cat in categories:
                if cat in CATEGORY_TO_TYPE:
                    issue_type = CATEGORY_TO_TYPE[cat]
                    break

            severity = SEVERITY_MAP.get(severity_str, "warning")

            issue = CatalogIssue(
                scan_id=scan.id,
                asin=asin,
                sku=sku,
                issue_type=issue_type,
                severity=severity,
                title=f"{issue_type.replace('_', ' ').title()}: {sku}",
                description=message[:500] if message else None,
                amazon_issue_code=code[:100] if code else None,
                fix_proposal=_generate_fix_proposal(issue_type, sku, issue_data),
            )
            db.add(issue)

        # Check for broken variations via child_parent_sku_relationship
        attributes = item.get("attributes", {})
        parent_sku_rel = attributes.get("child_parent_sku_relationship", [])
        if parent_sku_rel:
            for rel in parent_sku_rel:
                parent_sku = rel.get("value", {}).get("parent_sku", "") if isinstance(rel.get("value"), dict) else ""
                if parent_sku and parent_sku not in existing_skus:
                    issue = CatalogIssue(
                        scan_id=scan.id,
                        asin=asin,
                        sku=sku,
                        issue_type="broken_variation",
                        severity="critical",
                        title=f"Broken variation: {sku} → parent {parent_sku} not found",
                        description=f"Child SKU references parent SKU '{parent_sku}' which doesn't exist in catalog",
                    )
                    db.add(issue)

        # Update progress every 50 items
        if i > 0 and i % 50 == 0:
            pct = 50 + int((i / max(len(items), 1)) * 30)
            scan.progress = {"phase": "inspection", "percent": min(pct, 80), "detail": f"Inspected {i}/{len(items)} listings"}
            db.commit()

    db.commit()


async def _phase3_analysis(scan: CatalogScan, db: Session) -> None:
    """Phase 3: Cross-reference analysis and deduplication.

    WHY dedupe: Same SKU can appear in both FYP report (suppressed) and
    Listings API issues — keep the more detailed record.
    """
    scan.progress = {"phase": "analysis", "percent": 85, "detail": "Deduplicating issues..."}
    db.commit()

    # Deduplicate: if same SKU + issue_type exists from both report and API, keep API version (has more detail)
    all_issues = db.query(CatalogIssue).filter(CatalogIssue.scan_id == scan.id).all()

    seen: Dict[str, CatalogIssue] = {}
    to_delete: List[str] = []

    for issue in all_issues:
        key = f"{issue.sku}:{issue.issue_type}"
        if key in seen:
            existing = seen[key]
            # Keep the one with fix_proposal or amazon_issue_code (more actionable)
            if issue.fix_proposal and not existing.fix_proposal:
                to_delete.append(existing.id)
                seen[key] = issue
            elif issue.amazon_issue_code and not existing.amazon_issue_code:
                to_delete.append(existing.id)
                seen[key] = issue
            else:
                to_delete.append(issue.id)
        else:
            seen[key] = issue

    if to_delete:
        db.query(CatalogIssue).filter(CatalogIssue.id.in_(to_delete)).delete(synchronize_session="fetch")
        db.commit()
        logger.info("catalog_health_deduped", scan_id=scan.id, removed=len(to_delete))

    scan.progress = {"phase": "analysis", "percent": 95, "detail": "Finalizing..."}
    db.commit()


def _generate_fix_proposal(
    issue_type: str, sku: str, issue_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Generate a fix proposal for auto-fixable issues.

    WHY: missing_attribute issues can often be fixed with a PATCH operation.
    Other types need manual intervention.
    """
    if issue_type != "missing_attribute":
        return None

    attr_names = issue_data.get("attributeNames", [])
    if not attr_names:
        return None

    # WHY Listings API PATCH: Partial update — only set missing attributes
    patches = []
    for attr in attr_names:
        patches.append({
            "op": "replace",
            "path": f"/attributes/{attr}",
            "value": [],  # Placeholder — user needs to provide actual value
        })

    return {
        "action": "patch",
        "sku": sku,
        "patches": patches,
        "note": "Placeholder values — review before applying",
    }


async def apply_fix(
    issue_id: str, user_id: str, db: Session
) -> Dict[str, Any]:
    """Apply a fix proposal via Listings API PATCH.

    WHY one-at-a-time: Each fix needs individual review — batch apply is risky.
    """
    issue = db.query(CatalogIssue).filter(CatalogIssue.id == issue_id).first()
    if not issue:
        return {"error": "Issue not found"}

    scan = db.query(CatalogScan).filter(CatalogScan.id == issue.scan_id).first()
    if not scan or scan.user_id != user_id:
        return {"error": "Unauthorized"}

    if not issue.fix_proposal:
        return {"error": "No fix proposal available for this issue"}

    if issue.fix_status == "applied":
        return {"error": "Fix already applied"}

    proposal = issue.fix_proposal
    if proposal.get("action") != "patch" or not proposal.get("patches"):
        return {"error": "Fix proposal not applicable"}

    if not scan.seller_id:
        return {"error": "No seller_id — cannot apply fix"}

    # WHY product_type required: Listings API PATCH needs it
    product_type = proposal.get("product_type", "PRODUCT")

    result = await patch_listing(
        seller_id=scan.seller_id,
        sku=proposal["sku"],
        product_type=product_type,
        patches=proposal["patches"],
        marketplace=scan.marketplace,
        db=db,
        user_id=user_id,
    )

    if "error" in result:
        issue.fix_status = "failed"
        issue.fix_result = result
        db.commit()
        return {"error": result["error"], "fix_status": "failed"}

    issue.fix_status = "applied"
    issue.fix_result = result
    db.commit()

    # Update scan counter
    scan.issues_fixed = db.query(CatalogIssue).filter(
        CatalogIssue.scan_id == scan.id,
        CatalogIssue.fix_status == "applied",
    ).count()
    db.commit()

    return {"fix_status": "applied", "result": result}


async def get_dashboard_stats(user_id: str, db: Session) -> Dict[str, Any]:
    """Aggregate stats for the dashboard overview."""
    total_scans = db.query(CatalogScan).filter(CatalogScan.user_id == user_id).count()

    last_scan = (
        db.query(CatalogScan)
        .filter(CatalogScan.user_id == user_id)
        .order_by(CatalogScan.created_at.desc())
        .first()
    )

    # Aggregate issues from latest completed scan
    issues_by_type: Dict[str, int] = {}
    issues_by_severity: Dict[str, int] = {}
    total_issues = 0
    total_fixed = 0

    if last_scan and last_scan.status == "completed":
        issues = db.query(CatalogIssue).filter(CatalogIssue.scan_id == last_scan.id).all()
        for issue in issues:
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
            total_issues += 1
            if issue.fix_status == "applied":
                total_fixed += 1

    return {
        "total_scans": total_scans,
        "last_scan": last_scan,
        "issues_by_type": issues_by_type,
        "issues_by_severity": issues_by_severity,
        "total_issues": total_issues,
        "total_fixed": total_fixed,
    }


def get_scan_issues(
    scan_id: str, user_id: str, db: Session,
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get paginated issues for a scan."""
    scan = db.query(CatalogScan).filter(CatalogScan.id == scan_id).first()
    if not scan or scan.user_id != user_id:
        return {"issues": [], "total": 0}

    query = db.query(CatalogIssue).filter(CatalogIssue.scan_id == scan_id)

    if issue_type:
        query = query.filter(CatalogIssue.issue_type == issue_type)
    if severity:
        query = query.filter(CatalogIssue.severity == severity)

    total = query.count()
    issues = query.order_by(CatalogIssue.severity.asc()).offset(offset).limit(min(limit, 100)).all()

    return {"issues": issues, "total": total}


def _get_seller_connection(
    user_id: str, marketplace: str, db: Session
) -> Optional[OAuthConnection]:
    """Find active Amazon OAuth connection for user + marketplace."""
    return (
        db.query(OAuthConnection)
        .filter(
            OAuthConnection.user_id == user_id,
            OAuthConnection.provider == "amazon",
            OAuthConnection.status == "active",
        )
        .first()
    )
