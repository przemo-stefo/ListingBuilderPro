# backend/schemas/audit.py
# Purpose: Pydantic request/response models for product card audit
# NOT for: Audit logic or scraping

from pydantic import BaseModel, Field
from typing import Optional, List


class AuditRequest(BaseModel):
    """Request to audit a single product card."""
    url: Optional[str] = Field(None, description="Product URL (Allegro, Amazon, eBay)")
    asin: Optional[str] = Field(None, description="Amazon ASIN (alternative to URL)")
    marketplace: str = Field("allegro", description="allegro | amazon | ebay | kaufland")


class AuditIssue(BaseModel):
    """Single compliance issue found during audit."""
    field: str
    severity: str  # error | warning | info
    message: str
    fix_suggestion: Optional[str] = None  # WHY: AI-generated fix recommendation


class AuditResult(BaseModel):
    """Full audit result for one product."""
    source_url: str
    source_id: str
    marketplace: str
    product_title: str
    overall_status: str  # compliant | warning | error
    score: float  # 0-100
    issues: List[AuditIssue]
    product_data: dict  # WHY: Raw scraped data for frontend display
