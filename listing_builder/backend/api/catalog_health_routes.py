# backend/api/catalog_health_routes.py
# Purpose: REST endpoints for Catalog Health Check (scan, issues, fix)
# NOT for: Scan logic (catalog_health_service.py) or SP-API communication

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db, SessionLocal
from models.catalog_health import CatalogScan
from schemas.catalog_health import (
    ScanStartRequest,
    ScanResponse,
    ScanListResponse,
    CatalogIssueResponse,
    IssueListResponse,
    DashboardResponse,
    FixResultResponse,
)
from services.catalog_health_service import (
    start_scan,
    run_scan,
    get_dashboard_stats,
    get_scan_issues,
    apply_fix,
)
from services.sp_api_auth import credentials_configured, has_refresh_token
from api.dependencies import require_user_id, require_premium
from utils.validators import validate_uuid

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/catalog-health", tags=["Catalog Health"])


@router.get("/status")
async def catalog_health_status(_user_id: str = Depends(require_user_id)):
    """Check if Amazon SP-API credentials are configured for catalog health."""
    return {
        "credentials_configured": credentials_configured(),
        "has_refresh_token": has_refresh_token(),
    }


@router.post("/scan", response_model=ScanResponse, status_code=202)
@limiter.limit("3/minute")
async def start_catalog_scan(
    request: Request,
    body: ScanStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Start a new catalog health scan.

    WHY 202: Scan runs in background (Reports API takes minutes).
    Poll GET /scan/{id} for status.
    """
    require_premium(request, db)

    if not credentials_configured():
        raise HTTPException(status_code=400, detail="Amazon SP-API credentials not configured")
    if not has_refresh_token():
        raise HTTPException(status_code=400, detail="Amazon OAuth not connected — connect in Settings")

    # Check for existing running scan
    existing = (
        db.query(CatalogScan)
        .filter(
            CatalogScan.user_id == user_id,
            CatalogScan.status.in_(["pending", "scanning"]),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Scan already in progress")

    scan = await start_scan(user_id, body.marketplace, db)

    # WHY new SessionLocal: Background task outlives the request — needs its own session
    def _run_scan_bg(scan_id: str) -> None:
        import asyncio

        async def _run() -> None:
            bg_db = SessionLocal()
            try:
                await run_scan(scan_id, bg_db)
            finally:
                bg_db.close()

        asyncio.run(_run())

    background_tasks.add_task(_run_scan_bg, scan.id)

    logger.info("catalog_health_scan_started", scan_id=scan.id, marketplace=body.marketplace)
    return scan


@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan_status(
    scan_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get scan status and progress."""
    validate_uuid(scan_id, "scan_id")
    scan = db.query(CatalogScan).filter(CatalogScan.id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return scan


@router.get("/scan/{scan_id}/issues", response_model=IssueListResponse)
async def get_scan_issues_endpoint(
    scan_id: str,
    issue_type: str = Query(default=None),
    severity: str = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get paginated issues for a scan."""
    validate_uuid(scan_id, "scan_id")
    result = get_scan_issues(scan_id, user_id, db, issue_type=issue_type, severity=severity, offset=offset, limit=limit)
    return IssueListResponse(issues=result["issues"], total=result["total"])


@router.post("/fix/{issue_id}", response_model=FixResultResponse)
@limiter.limit("10/minute")
async def apply_issue_fix(
    request: Request,
    issue_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Apply a fix proposal for an issue via Listings API.

    WHY rate limit: Each fix calls SP-API PATCH — prevent abuse.
    """
    require_premium(request, db)
    validate_uuid(issue_id, "issue_id")
    result = await apply_fix(issue_id, user_id, db)

    if "error" in result:
        status_code = 404 if result["error"] == "Issue not found" else 400
        if result["error"] == "Unauthorized":
            status_code = 403
        raise HTTPException(status_code=status_code, detail=result["error"])

    return FixResultResponse(
        issue_id=issue_id,
        fix_status=result["fix_status"],
        fix_result=result.get("result"),
        message="Fix applied successfully",
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get dashboard overview stats."""
    stats = await get_dashboard_stats(user_id, db)
    return DashboardResponse(**stats)


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List user's scan history."""
    query = db.query(CatalogScan).filter(CatalogScan.user_id == user_id)
    total = query.count()
    scans = query.order_by(CatalogScan.created_at.desc()).offset(offset).limit(limit).all()
    return ScanListResponse(scans=scans, total=total)
