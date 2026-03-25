# backend/services/catalog_health_service.py
# Purpose: Public API for Catalog Health — queries, fixes, dashboard
# NOT for: Scan pipeline phases (catalog_health_scanner.py) or API routes

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.catalog_health import CatalogScan, CatalogIssue
from models.oauth_connection import OAuthConnection
from services.sp_api_auth import credentials_configured
from services.sp_api_listings import patch_listing
# WHY re-export: Routes import run_scan from this module
from services.catalog_health_scanner import run_scan  # noqa: F401

logger = structlog.get_logger()


async def start_scan(user_id: str, marketplace: str, db: Session) -> CatalogScan:
    """Create a new scan record in pending state."""
    connection = _get_seller_connection(user_id, marketplace, db)
    scan = CatalogScan(
        user_id=user_id,
        marketplace=marketplace.upper(),
        seller_id=connection.seller_id if connection else None,
        status="pending",
        progress={"phase": "waiting", "percent": 0},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


async def apply_fix(issue_id: str, user_id: str, db: Session) -> Dict[str, Any]:
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

    result = await patch_listing(
        seller_id=scan.seller_id,
        sku=proposal["sku"],
        product_type=proposal.get("product_type", "PRODUCT"),
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

    scan.issues_fixed = db.query(CatalogIssue).filter(
        CatalogIssue.scan_id == scan.id,
        CatalogIssue.fix_status == "applied",
    ).count()
    db.commit()

    return {"fix_status": "applied", "result": result}


async def get_dashboard_stats(user_id: str, db: Session) -> Dict[str, Any]:
    """Aggregate stats for the dashboard overview.

    WHY GROUP BY: Aggregate in DB instead of loading all rows into Python.
    """
    total_scans = db.query(CatalogScan).filter(CatalogScan.user_id == user_id).count()
    last_scan = (
        db.query(CatalogScan)
        .filter(CatalogScan.user_id == user_id)
        .order_by(CatalogScan.created_at.desc())
        .first()
    )

    issues_by_type: Dict[str, int] = {}
    issues_by_severity: Dict[str, int] = {}
    total_issues = 0
    total_fixed = 0

    if last_scan and last_scan.status == "completed":
        scan_filter = CatalogIssue.scan_id == last_scan.id

        type_counts = (
            db.query(CatalogIssue.issue_type, func.count())
            .filter(scan_filter).group_by(CatalogIssue.issue_type).all()
        )
        issues_by_type = {t: c for t, c in type_counts}

        sev_counts = (
            db.query(CatalogIssue.severity, func.count())
            .filter(scan_filter).group_by(CatalogIssue.severity).all()
        )
        issues_by_severity = {s: c for s, c in sev_counts}

        total_issues = sum(issues_by_type.values())
        total_fixed = (
            db.query(func.count()).select_from(CatalogIssue)
            .filter(scan_filter, CatalogIssue.fix_status == "applied")
            .scalar() or 0
        )

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


def _get_seller_connection(user_id: str, marketplace: str, db: Session) -> Optional[OAuthConnection]:
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
