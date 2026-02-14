# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/api/compliance_routes.py
# Purpose: API endpoints for compliance template validation
# NOT for: Parsing logic, rules, or database models

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from services.compliance import ComplianceService
from schemas.compliance import (
    ComplianceReportResponse,
    ComplianceItemResult,
    ComplianceIssue,
    ComplianceReportsListResponse,
    ComplianceReportSummary,
)
from schemas.audit import AuditRequest, AuditResult
from services.audit_service import audit_product
from typing import Optional
import structlog

logger = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

# WHY 10MB limit: Amazon XLSM templates can be 3-5MB with macros,
# but anything over 10MB is likely not a valid template file.
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {".xlsm", ".xlsx", ".csv"}


@router.post("/validate", status_code=201)
@limiter.limit("5/minute")
async def validate_template(
    request: Request,
    file: UploadFile = File(..., description="XLSM, XLSX, or CSV template file"),
    marketplace: Optional[str] = Query(
        None,
        description="Force marketplace (amazon/ebay/kaufland). Auto-detected from extension if not provided.",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a marketplace template file and get a compliance validation report.

    Supported formats:
    - Amazon: .xlsm (Flat File template)
    - eBay: .xlsx (Bulk listing template)
    - Kaufland: .csv (Product data template)

    Returns a full report with per-product compliance issues.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filename = file.filename.strip()
    ext = _get_extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file bytes with size check
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f}MB). Max: 10MB",
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    logger.info("compliance_upload_received", filename=filename, size=len(file_bytes))

    # Run validation
    try:
        service = ComplianceService(db)
        report = service.validate_file(file_bytes, filename, marketplace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("compliance_validation_failed", error=str(e), filename=filename)
        raise HTTPException(status_code=500, detail="Validation failed")

    # Build response from ORM objects
    return _report_to_response(report)


@router.get("/reports", response_model=ComplianceReportsListResponse)
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    db: Session = Depends(get_db),
):
    """List past compliance reports with pagination."""
    service = ComplianceService(db)
    reports, total = service.get_reports(limit=limit, offset=offset, marketplace=marketplace)

    return ComplianceReportsListResponse(
        items=[
            ComplianceReportSummary(
                id=r.id,
                marketplace=r.marketplace,
                filename=r.filename,
                total_products=r.total_products,
                compliant_count=r.compliant_count,
                warning_count=r.warning_count,
                error_count=r.error_count,
                overall_score=r.overall_score,
                created_at=r.created_at,
            )
            for r in reports
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/reports/{report_id}", response_model=ComplianceReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get a single compliance report with all product items."""
    service = ComplianceService(db)
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return _report_to_response(report)


def _report_to_response(report) -> ComplianceReportResponse:
    """Convert ORM report + items to Pydantic response."""
    return ComplianceReportResponse(
        id=report.id,
        marketplace=report.marketplace,
        filename=report.filename,
        total_products=report.total_products,
        compliant_count=report.compliant_count,
        warning_count=report.warning_count,
        error_count=report.error_count,
        overall_score=report.overall_score,
        created_at=report.created_at,
        items=[
            ComplianceItemResult(
                row_number=item.row_number,
                sku=item.sku,
                product_title=item.product_title,
                status=item.compliance_status,
                issues=[
                    ComplianceIssue(**issue)
                    for issue in (item.issues or [])
                ],
            )
            for item in (report.items or [])
        ],
    )


@router.post("/audit", response_model=AuditResult)
@limiter.limit("10/minute")
async def audit_product_card(request: Request, body: AuditRequest):
    """
    Audit a single product card by URL or ASIN.

    Scrapes the product page, runs compliance checks,
    and returns issues with AI-generated fix suggestions.
    """
    url = body.url
    marketplace = body.marketplace.lower()

    # WHY: ASIN → build Amazon URL (for future Amazon scraper support)
    if body.asin and not url:
        url = f"https://www.amazon.de/dp/{body.asin}"
        marketplace = "amazon"

    if not url:
        raise HTTPException(status_code=400, detail="URL lub ASIN jest wymagany")

    try:
        result = await audit_product(url, marketplace)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("audit_failed", url=url, error=str(e))
        # SECURITY: Don't leak internal error details to client
        raise HTTPException(status_code=500, detail="Audit failed")


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()
