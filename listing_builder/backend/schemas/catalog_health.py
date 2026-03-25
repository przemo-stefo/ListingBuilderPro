# backend/schemas/catalog_health.py
# Purpose: Pydantic schemas for Catalog Health Check API
# NOT for: Database models (models/catalog_health.py)

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ALLOWED_MARKETPLACES = ("DE", "FR", "IT", "ES", "PL", "NL", "SE", "BE", "UK", "US")


class ScanStartRequest(BaseModel):
    marketplace: Literal["DE", "FR", "IT", "ES", "PL", "NL", "SE", "BE", "UK", "US"] = Field(
        default="DE", description="Amazon marketplace code"
    )


class ScanResponse(BaseModel):
    id: str
    user_id: str
    marketplace: str
    seller_id: Optional[str] = None
    status: str
    progress: Optional[Dict[str, Any]] = None
    total_listings: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int


class CatalogIssueResponse(BaseModel):
    id: str
    scan_id: str
    asin: Optional[str] = None
    sku: Optional[str] = None
    issue_type: str
    severity: str
    title: str
    description: Optional[str] = None
    amazon_issue_code: Optional[str] = None
    fix_proposal: Optional[Dict[str, Any]] = None
    fix_status: str = "pending"
    fix_result: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    issues: List[CatalogIssueResponse]
    total: int


class DashboardResponse(BaseModel):
    total_scans: int = 0
    last_scan: Optional[ScanResponse] = None
    issues_by_type: Dict[str, int] = {}
    issues_by_severity: Dict[str, int] = {}
    total_issues: int = 0
    total_fixed: int = 0


class FixResultResponse(BaseModel):
    issue_id: str
    fix_status: str
    fix_result: Optional[Dict[str, Any]] = None
    message: str
