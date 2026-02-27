# backend/api/epr_routes.py
# Purpose: REST endpoints for EPR report management (fetch, list, detail, delete)
# NOT for: SP-API communication or CSV parsing

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db, SessionLocal
from models.epr import EprReport, EprReportRow
from models.epr_country import EprCountryRule
from schemas.epr import (
    EprFetchRequest,
    EprReportResponse,
    EprReportsListResponse,
    EprStatusResponse,
    EprCountryRuleResponse,
    EprCountryRulesListResponse,
)
from services.sp_api_auth import credentials_configured, has_refresh_token
from services.epr_service import fetch_epr_report_pipeline
from api.dependencies import require_user_id
from utils.validators import validate_uuid

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/epr", tags=["EPR Reports"])


@router.get("/status", response_model=EprStatusResponse)
async def epr_status(_user_id: str = Depends(require_user_id)):
    """Check if Amazon SP-API credentials are configured.
    WHY require_user_id: Prevents unauthenticated probing of server credential state.
    """
    return EprStatusResponse(
        credentials_configured=credentials_configured(),
        has_refresh_token=has_refresh_token(),
    )


@router.post("/fetch", response_model=EprReportResponse, status_code=202)
@limiter.limit("5/minute")
async def fetch_epr_report(
    request: Request,
    body: EprFetchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """
    Start fetching an EPR report from Amazon SP-API.
    Returns immediately with status=pending; polling happens in background.
    """
    if not has_refresh_token():
        raise HTTPException(status_code=400, detail="Refresh token not configured")
    if not credentials_configured():
        raise HTTPException(status_code=400, detail="Amazon SP-API credentials not configured")

    # Create DB record
    report = EprReport(
        user_id=user_id,
        report_type=body.report_type,
        marketplace_id=body.marketplace_ids[0],
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # WHY BackgroundTasks: polling SP-API takes minutes, don't block the HTTP response
    # WHY new session: background task outlives the request session
    def _run_pipeline():
        import asyncio
        bg_db = SessionLocal()
        try:
            bg_report = bg_db.query(EprReport).get(report.id)
            asyncio.run(fetch_epr_report_pipeline(bg_db, bg_report, body.marketplace_ids))
        finally:
            bg_db.close()

    background_tasks.add_task(_run_pipeline)

    logger.info("epr_fetch_started", report_id=report.id, report_type=body.report_type)
    return report


@router.get("/reports", response_model=EprReportsListResponse)
async def list_epr_reports(db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """List all EPR reports, newest first."""
    reports = (
        db.query(EprReport)
        .filter(EprReport.user_id == user_id)
        .order_by(EprReport.created_at.desc())
        .limit(50)
        .all()
    )
    return EprReportsListResponse(reports=reports, total=len(reports))


@router.get("/reports/{report_id}", response_model=EprReportResponse)
async def get_epr_report(report_id: str, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Get a single EPR report with all rows."""
    validate_uuid(report_id, "report_id")
    report = db.query(EprReport).filter(EprReport.id == report_id, EprReport.user_id == user_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # WHY manual rows: eagerly load for response
    response = EprReportResponse.model_validate(report)
    response.rows = [
        row for row in report.rows
    ]
    return response


@router.delete("/reports/{report_id}", status_code=204)
async def delete_epr_report(report_id: str, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    """Delete an EPR report and its rows (CASCADE)."""
    validate_uuid(report_id, "report_id")
    report = db.query(EprReport).filter(EprReport.id == report_id, EprReport.user_id == user_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    logger.info("epr_report_deleted", report_id=report_id)


# ── Country rules endpoints ──────────────────────────────────────────────────


@router.get("/countries", response_model=EprCountryRulesListResponse)
async def list_country_rules(db: Session = Depends(get_db)):
    """List all EPR country rules (7 countries × 3 categories)."""
    rules = (
        db.query(EprCountryRule)
        .order_by(EprCountryRule.country_code, EprCountryRule.category)
        .all()
    )
    return EprCountryRulesListResponse(rules=rules, total=len(rules))


@router.get("/countries/{country_code}", response_model=EprCountryRulesListResponse)
async def get_country_rules(country_code: str, db: Session = Depends(get_db)):
    """Get EPR rules for a specific country (3 categories)."""
    rules = (
        db.query(EprCountryRule)
        .filter(EprCountryRule.country_code == country_code.upper())
        .order_by(EprCountryRule.category)
        .all()
    )
    if not rules:
        raise HTTPException(status_code=404, detail=f"No rules for country: {country_code}")
    return EprCountryRulesListResponse(rules=rules, total=len(rules))
