# backend/schemas/epr.py
# Purpose: Pydantic request/response models for EPR endpoints
# NOT for: Database models or SP-API logic

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Requests ──

class EprFetchRequest(BaseModel):
    """Request to fetch an EPR report from SP-API."""
    report_type: str = Field(
        default="GET_EPR_MONTHLY_REPORTS",
        description="SP-API report type: GET_EPR_MONTHLY_REPORTS or GET_EPR_STATUS",
    )
    marketplace_ids: List[str] = Field(
        default=["A1PA6795UKMFR9"],
        description="Amazon marketplace IDs (default: DE)",
    )


# ── Responses ──

class EprReportRowResponse(BaseModel):
    """Single row from an EPR report."""
    id: str
    asin: Optional[str] = None
    marketplace: Optional[str] = None
    epr_category: Optional[str] = None
    registration_number: Optional[str] = None
    paper_kg: float = 0
    glass_kg: float = 0
    aluminum_kg: float = 0
    steel_kg: float = 0
    plastic_kg: float = 0
    wood_kg: float = 0
    units_sold: int = 0
    reporting_period: Optional[str] = None

    class Config:
        from_attributes = True


class EprReportResponse(BaseModel):
    """EPR report metadata + optional rows."""
    id: str
    report_type: str
    marketplace_id: str
    status: str
    sp_api_report_id: Optional[str] = None
    row_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    rows: Optional[List[EprReportRowResponse]] = None

    class Config:
        from_attributes = True


class EprReportsListResponse(BaseModel):
    """List of EPR reports."""
    reports: List[EprReportResponse]
    total: int


class EprStatusResponse(BaseModel):
    """Credentials configuration status."""
    credentials_configured: bool
    has_refresh_token: bool
