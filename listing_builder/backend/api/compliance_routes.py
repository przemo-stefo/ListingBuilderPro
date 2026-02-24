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
from services.audit_service import audit_product, audit_product_from_data
from services.allegro_api import fetch_seller_offers, fetch_offer_details
from api.dependencies import get_user_id, require_premium
from models.compliance import ComplianceReport, ComplianceReportItem
from models.oauth_connection import OAuthConnection
from typing import Optional
import asyncio
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

    require_premium(request, db)

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
async def audit_product_card(request: Request, body: AuditRequest, db: Session = Depends(get_db)):
    """
    Audit a single product card by URL or ASIN.

    Scrapes the product page, runs compliance checks,
    and returns issues with AI-generated fix suggestions.
    """
    require_premium(request, db)
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


MAX_STORE_SCAN = 50  # WHY: 50 parallel API calls is safe for Allegro rate limits


@router.post("/audit-store", response_model=ComplianceReportResponse)
@limiter.limit("2/minute")
async def audit_store(request: Request, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    """Scan connected Allegro store — fetch offers via API, audit each, save report."""
    require_premium(request, db)

    # Step 1: Verify Allegro OAuth is active + get access token
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id,
        OAuthConnection.marketplace == "allegro",
    ).first()

    if not conn or conn.status != "active":
        raise HTTPException(status_code=400, detail="Allegro nie jest połączone")

    # Step 2: Fetch seller offers (list of URLs)
    offers_data = await fetch_seller_offers(db, user_id)
    if offers_data.get("error"):
        raise HTTPException(status_code=400, detail=offers_data["error"])

    urls = offers_data.get("urls", [])
    if not urls:
        raise HTTPException(status_code=400, detail="Brak aktywnych ofert na koncie Allegro")

    # WHY: Cap at 50 — more would be slow and hit Allegro rate limits
    capped_urls = urls[:MAX_STORE_SCAN]
    offer_ids = [url.split("/")[-1] for url in capped_urls]

    logger.info("audit_store_start", total_offers=len(urls), scanning=len(offer_ids))

    # Step 3: Fetch details for each offer (parallel, batched)
    access_token = conn.access_token

    async def fetch_and_audit(oid: str) -> dict:
        detail = await fetch_offer_details(oid, access_token)
        if detail.get("error"):
            return {
                "source_id": oid, "product_title": f"Oferta {oid}",
                "overall_status": "error", "score": 0,
                "issues": [{"field": "api", "severity": "error",
                            "message": detail["error"]}],
            }
        return audit_product_from_data(detail)

    # WHY: semaphore limits concurrent Allegro API calls to avoid 429
    sem = asyncio.Semaphore(10)

    async def limited_fetch(oid: str) -> dict:
        async with sem:
            return await fetch_and_audit(oid)

    results = await asyncio.gather(*[limited_fetch(oid) for oid in offer_ids])

    # Step 4: Calculate aggregate stats
    compliant = sum(1 for r in results if r["overall_status"] == "compliant")
    warnings = sum(1 for r in results if r["overall_status"] == "warning")
    errors = sum(1 for r in results if r["overall_status"] == "error")
    avg_score = round(sum(r["score"] for r in results) / max(len(results), 1), 1)

    # Step 5: Save as ComplianceReport + items
    report = ComplianceReport(
        marketplace="allegro",
        filename=f"Skan sklepu Allegro ({len(results)} produktów)",
        total_products=len(results),
        compliant_count=compliant,
        warning_count=warnings,
        error_count=errors,
        overall_score=avg_score,
    )
    db.add(report)

    for idx, r in enumerate(results, start=1):
        item = ComplianceReportItem(
            report_id=report.id,
            row_number=idx,
            sku=r.get("source_id", ""),
            product_title=r.get("product_title", ""),
            compliance_status=r["overall_status"],
            issues=r.get("issues", []),
        )
        db.add(item)

    db.commit()
    db.refresh(report)

    logger.info("audit_store_done", report_id=report.id, score=avg_score,
                compliant=compliant, warnings=warnings, errors=errors)

    return _report_to_response(report)


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()
