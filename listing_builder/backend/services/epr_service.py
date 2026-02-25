# backend/services/epr_service.py
# Purpose: Fetch, poll, download and parse EPR reports from Amazon SP-API
# NOT for: Token management (sp_api_auth) or API routing (epr_routes)

import asyncio
import csv
import io
import httpx
import structlog
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from models.epr import EprReport, EprReportRow
from services.sp_api_auth import get_access_token

logger = structlog.get_logger()

SP_API_BASE = "https://sellingpartnerapi-eu.amazon.com"
REPORTS_API = f"{SP_API_BASE}/reports/2021-06-30"

# WHY these two: only EPR-related report types in SP-API
VALID_REPORT_TYPES = {"GET_EPR_MONTHLY_REPORTS", "GET_EPR_STATUS"}

# Polling config
MAX_POLL_ATTEMPTS = 10
POLL_INTERVAL_SECONDS = 30


async def _sp_api_headers() -> dict:
    """Build auth headers for SP-API calls."""
    token = await get_access_token()
    return {
        "x-amz-access-token": token,
        "Content-Type": "application/json",
    }


async def create_report(report_type: str, marketplace_ids: List[str]) -> str:
    """
    Request a new report from SP-API.
    Returns the SP-API reportId.
    """
    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(f"Invalid report type: {report_type}. Valid: {VALID_REPORT_TYPES}")

    headers = await _sp_api_headers()
    body = {
        "reportType": report_type,
        "marketplaceIds": marketplace_ids,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{REPORTS_API}/reports", json=body, headers=headers)

    if resp.status_code not in (200, 202):
        logger.error("epr_create_report_failed", status=resp.status_code)
        raise RuntimeError(f"createReport failed: {resp.status_code}")

    data = resp.json()
    report_id = data.get("reportId")
    if not report_id:
        raise RuntimeError(f"createReport returned no reportId: {data}")

    logger.info("epr_report_created", report_id=report_id, report_type=report_type)
    return report_id


async def poll_report(sp_report_id: str) -> Optional[str]:
    """
    Poll SP-API until report is DONE. Returns reportDocumentId.
    Returns None if report fails or times out.
    """
    for attempt in range(MAX_POLL_ATTEMPTS):
        headers = await _sp_api_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{REPORTS_API}/reports/{sp_report_id}", headers=headers)

        if resp.status_code != 200:
            logger.warning("epr_poll_error", status=resp.status_code, attempt=attempt)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            continue

        data = resp.json()
        status = data.get("processingStatus")

        if status == "DONE":
            doc_id = data.get("reportDocumentId")
            logger.info("epr_report_done", doc_id=doc_id)
            return doc_id

        if status in ("CANCELLED", "FATAL"):
            logger.error("epr_report_failed", status=status, report_id=sp_report_id)
            return None

        logger.info("epr_report_polling", status=status, attempt=attempt)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    logger.error("epr_report_poll_timeout", report_id=sp_report_id)
    return None


async def download_report(document_id: str) -> str:
    """
    Get report document URL from SP-API and download CSV content.
    Returns raw CSV text.
    """
    headers = await _sp_api_headers()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{REPORTS_API}/documents/{document_id}", headers=headers)

    if resp.status_code != 200:
        logger.error("epr_get_document_failed", status=resp.status_code)
        raise RuntimeError(f"getDocument failed: {resp.status_code}")

    data = resp.json()
    download_url = data.get("url")
    if not download_url:
        raise RuntimeError(f"No download URL in document: {data}")

    # WHY separate download: SP-API returns a pre-signed S3 URL
    async with httpx.AsyncClient(timeout=60) as client:
        dl_resp = await client.get(download_url)

    if dl_resp.status_code != 200:
        raise RuntimeError(f"CSV download failed: {dl_resp.status_code}")

    logger.info("epr_report_downloaded", doc_id=document_id, size=len(dl_resp.text))
    return dl_resp.text


def parse_epr_csv(csv_text: str) -> List[dict]:
    """
    Parse EPR report CSV into list of dicts.
    Column names are normalized to snake_case.
    """
    reader = csv.DictReader(io.StringIO(csv_text), delimiter="\t")
    rows = []

    for row in reader:
        parsed = {
            "asin": row.get("asin", ""),
            "marketplace": row.get("marketplace", ""),
            "epr_category": row.get("eprCategory", row.get("epr_category", "")),
            "registration_number": row.get("registrationNumber", row.get("registration_number", "")),
            "paper_kg": _safe_float(row.get("paperInGrams", row.get("paper_kg", 0))) / 1000,
            "glass_kg": _safe_float(row.get("glassInGrams", row.get("glass_kg", 0))) / 1000,
            "aluminum_kg": _safe_float(row.get("aluminumInGrams", row.get("aluminum_kg", 0))) / 1000,
            "steel_kg": _safe_float(row.get("steelInGrams", row.get("steel_kg", 0))) / 1000,
            "plastic_kg": _safe_float(row.get("plasticInGrams", row.get("plastic_kg", 0))) / 1000,
            "wood_kg": _safe_float(row.get("woodInGrams", row.get("wood_kg", 0))) / 1000,
            "units_sold": int(_safe_float(row.get("unitsSold", row.get("units_sold", 0)))),
            "reporting_period": row.get("reportingPeriod", row.get("reporting_period", "")),
        }
        rows.append(parsed)

    return rows


def _safe_float(val) -> float:
    """Convert to float, defaulting to 0 on failure."""
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0


def save_report(db: Session, rows: List[dict], report: EprReport) -> EprReport:
    """Save parsed CSV rows into DB, update report status."""
    for row_data in rows:
        db_row = EprReportRow(report_id=report.id, **row_data)
        db.add(db_row)

    report.status = "done"
    report.row_count = len(rows)
    report.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)

    logger.info("epr_report_saved", report_id=report.id, row_count=len(rows))
    return report


async def fetch_epr_report_pipeline(db: Session, report: EprReport, marketplace_ids: List[str]):
    """
    Full background pipeline: create → poll → download → parse → save.
    Updates report status on failure.
    """
    try:
        # Step 1: Create report request
        sp_report_id = await create_report(report.report_type, marketplace_ids)
        report.sp_api_report_id = sp_report_id
        report.status = "processing"
        db.commit()

        # Step 2: Poll until done
        doc_id = await poll_report(sp_report_id)
        if not doc_id:
            report.status = "failed"
            report.error_message = "Report processing failed or timed out"
            db.commit()
            return

        # Step 3: Download CSV
        csv_text = await download_report(doc_id)

        # Step 4: Parse + save
        rows = parse_epr_csv(csv_text)
        save_report(db, rows, report)

    except Exception as e:
        logger.error("epr_pipeline_failed", report_id=report.id, error=str(e))
        report.status = "failed"
        report.error_message = str(e)[:500]
        db.commit()
