# backend/services/sp_api_reports.py
# Purpose: Amazon SP-API Reports API v2021-06-30 — create, poll, download reports
# NOT for: EPR-specific reports (epr_service.py) or catalog reads (sp_api_catalog.py)

import asyncio
import csv
import gzip
import io
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
import structlog
from sqlalchemy.orm import Session

from config import settings
from services.sp_api_auth import get_access_token, credentials_configured
from services.sp_api_catalog import SP_API_BASE_PROD, SP_API_BASE_SANDBOX, MARKETPLACE_IDS

logger = structlog.get_logger()

REPORTS_API_VERSION = "2021-06-30"

# WHY allowlist: Only catalog-health-related report types — prevents misuse
CATALOG_REPORT_TYPES = {
    "GET_MERCHANT_LISTINGS_ALL_DATA",
    "GET_MERCHANTS_LISTINGS_FYP_REPORT",
    "GET_STRANDED_INVENTORY_UI_DATA",
    "GET_MERCHANT_LISTINGS_INACTIVE_DATA",
}


def _base_url() -> str:
    return SP_API_BASE_SANDBOX if settings.amazon_sandbox else SP_API_BASE_PROD


def _headers(token: str) -> Dict[str, str]:
    return {"x-amz-access-token": token, "Content-Type": "application/json"}


async def create_report(
    report_type: str,
    marketplace_ids: List[str],
    user_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[str]:
    """Create a report request via SP-API Reports API.

    WHY async pipeline: Reports take 30s-15min to generate.
    Returns report_id for polling.
    """
    if report_type not in CATALOG_REPORT_TYPES:
        logger.error("sp_api_reports_invalid_type", report_type=report_type)
        return None

    if not credentials_configured():
        return None

    try:
        token = await get_access_token(db=db, user_id=user_id or "")
    except (ValueError, RuntimeError) as e:
        logger.error("sp_api_reports_auth_error", error=str(e)[:100])
        return None

    url = f"{_base_url()}/reports/{REPORTS_API_VERSION}/reports"
    body = {
        "reportType": report_type,
        "marketplaceIds": marketplace_ids,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=_headers(token), json=body)

        if resp.status_code in (200, 202):
            report_id = resp.json().get("reportId")
            logger.info("sp_api_report_created", report_type=report_type, report_id=report_id)
            return report_id

        logger.warning("sp_api_report_create_failed", status=resp.status_code, body=resp.text[:200])
        return None
    except Exception as e:
        logger.error("sp_api_report_create_error", error=str(e)[:100])
        return None


async def poll_report(
    report_id: str,
    max_attempts: int = 30,
    interval: int = 10,
    user_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[str]:
    """Poll report status until DONE, return reportDocumentId.

    WHY polling: SP-API reports are async — no webhook callback available.
    30 attempts * 10s = 5 min max wait.
    """
    if not credentials_configured():
        return None

    try:
        token = await get_access_token(db=db, user_id=user_id or "")
    except (ValueError, RuntimeError):
        return None

    url = f"{_base_url()}/reports/{REPORTS_API_VERSION}/reports/{report_id}"

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=_headers(token))

            if resp.status_code != 200:
                logger.warning("sp_api_report_poll_error", status=resp.status_code, attempt=attempt)
                await asyncio.sleep(interval)
                continue

            data = resp.json()
            status = data.get("processingStatus", "")

            if status == "DONE":
                doc_id = data.get("reportDocumentId")
                logger.info("sp_api_report_done", report_id=report_id, doc_id=doc_id)
                return doc_id

            if status in ("CANCELLED", "FATAL"):
                logger.error("sp_api_report_failed", report_id=report_id, status=status)
                return None

            # IN_QUEUE or IN_PROGRESS — keep polling
            await asyncio.sleep(interval)

        except Exception as e:
            logger.error("sp_api_report_poll_exception", error=str(e)[:100], attempt=attempt)
            await asyncio.sleep(interval)

    logger.error("sp_api_report_timeout", report_id=report_id, attempts=max_attempts)
    return None


async def download_report(
    document_id: str,
    user_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[str]:
    """Download report document content (handles gzip compression).

    WHY two-step: SP-API returns a presigned S3 URL in getReportDocument,
    then we fetch the actual content from that URL.
    """
    if not credentials_configured():
        return None

    try:
        token = await get_access_token(db=db, user_id=user_id or "")
    except (ValueError, RuntimeError):
        return None

    url = f"{_base_url()}/reports/{REPORTS_API_VERSION}/documents/{document_id}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=_headers(token))

        if resp.status_code != 200:
            logger.error("sp_api_report_doc_error", status=resp.status_code)
            return None

        data = resp.json()
        download_url = data.get("url", "")
        compression = data.get("compressionAlgorithm", "")

        # WHY URL validation: Prevent SSRF — only allow Amazon S3 domains
        parsed = urlparse(download_url)
        if not parsed.hostname or not (
            parsed.hostname.endswith(".amazonaws.com")
            or parsed.hostname.endswith(".amazon.com")
        ):
            logger.error("sp_api_report_suspicious_url", hostname=parsed.hostname)
            return None

        async with httpx.AsyncClient(timeout=60) as client:
            doc_resp = await client.get(download_url)

        if doc_resp.status_code != 200:
            logger.error("sp_api_report_download_error", status=doc_resp.status_code)
            return None

        content = doc_resp.content
        if compression == "GZIP":
            content = gzip.decompress(content)

        return content.decode("utf-8", errors="replace")

    except Exception as e:
        logger.error("sp_api_report_download_exception", error=str(e)[:100])
        return None


def parse_tsv_report(content: str) -> List[Dict[str, str]]:
    """Parse TSV report content into list of dicts.

    WHY TSV: Most SP-API reports use tab-separated format.
    """
    if not content or not content.strip():
        return []

    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    return [row for row in reader]


async def fetch_report_pipeline(
    report_type: str,
    marketplace_ids: List[str],
    user_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[List[Dict[str, str]]]:
    """Full pipeline: create -> poll -> download -> parse.

    WHY single function: Callers don't need to manage the 4-step process.
    """
    report_id = await create_report(report_type, marketplace_ids, user_id=user_id, db=db)
    if not report_id:
        return None

    doc_id = await poll_report(report_id, user_id=user_id, db=db)
    if not doc_id:
        return None

    content = await download_report(doc_id, user_id=user_id, db=db)
    if not content:
        return None

    return parse_tsv_report(content)
