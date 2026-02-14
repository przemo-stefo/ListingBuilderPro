# backend/schemas/audit.py
# Purpose: Pydantic request/response models for product card audit
# NOT for: Audit logic or scraping

import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

# WHY: ASIN is always exactly 10 alphanumeric characters
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


class AuditRequest(BaseModel):
    """Request to audit a single product card."""
    url: Optional[str] = Field(None, description="Product URL (Allegro, Amazon, eBay)")
    asin: Optional[str] = Field(None, description="Amazon ASIN (alternative to URL)")
    marketplace: str = Field("allegro", description="allegro | amazon | ebay | kaufland")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v, info):
        if not v:
            return v
        # SECURITY: Validate URL domain to prevent SSRF
        from utils.url_validator import validate_marketplace_url
        marketplace = info.data.get("marketplace", "allegro")
        return validate_marketplace_url(v, marketplace.lower())

    @field_validator("asin")
    @classmethod
    def validate_asin(cls, v):
        if not v:
            return v
        # SECURITY: Strict ASIN format prevents URL injection via ASIN field
        if not ASIN_PATTERN.match(v.upper()):
            raise ValueError("ASIN must be exactly 10 alphanumeric characters")
        return v.upper()


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
