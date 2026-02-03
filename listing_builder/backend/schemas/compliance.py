# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/schemas/compliance.py
# Purpose: Pydantic request/response models for compliance validation API
# NOT for: Database models or validation rule logic

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SeverityEnum(str, Enum):
    """Issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ComplianceStatusEnum(str, Enum):
    """Per-product compliance status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    ERROR = "error"


class MarketplaceEnum(str, Enum):
    """Supported marketplaces"""
    AMAZON = "amazon"
    EBAY = "ebay"
    KAUFLAND = "kaufland"


class ComplianceIssue(BaseModel):
    """Single compliance issue found on a product"""
    field: str = Field(..., description="Template field name that has the issue")
    rule: str = Field(..., description="Rule ID that was violated")
    severity: SeverityEnum
    message: str = Field(..., description="Human-readable explanation")


class ComplianceItemResult(BaseModel):
    """Compliance result for a single product row"""
    row_number: int
    sku: str = ""
    product_title: str = ""
    status: ComplianceStatusEnum
    issues: List[ComplianceIssue] = Field(default_factory=list)


class ComplianceReportResponse(BaseModel):
    """Full compliance report with all product items"""
    id: str
    marketplace: str
    filename: str
    total_products: int
    compliant_count: int
    warning_count: int
    error_count: int
    overall_score: float
    created_at: datetime
    items: List[ComplianceItemResult] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ComplianceReportSummary(BaseModel):
    """Report summary without items (for list endpoint)"""
    id: str
    marketplace: str
    filename: str
    total_products: int
    compliant_count: int
    warning_count: int
    error_count: int
    overall_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceReportsListResponse(BaseModel):
    """Paginated list of compliance reports"""
    items: List[ComplianceReportSummary]
    total: int
    limit: int
    offset: int
