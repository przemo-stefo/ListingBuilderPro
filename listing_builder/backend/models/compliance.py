# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/models/compliance.py
# Purpose: SQLAlchemy ORM models for compliance reports and per-product results
# NOT for: Validation rules, parsing logic, or API routes

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ComplianceReport(Base):
    """
    One report = one uploaded file validated.
    Stores aggregate stats (how many products passed/failed).
    """
    __tablename__ = "compliance_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    marketplace = Column(String(50), nullable=False, index=True)  # amazon, ebay, kaufland
    filename = Column(String(500), nullable=False)

    # Aggregate stats
    total_products = Column(Integer, default=0)
    compliant_count = Column(Integer, default=0)  # No issues
    warning_count = Column(Integer, default=0)    # Warnings only
    error_count = Column(Integer, default=0)      # Has errors

    # 0-100 score: (compliant / total) * 100
    overall_score = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to per-product items
    items = relationship(
        "ComplianceReportItem",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ComplianceReportItem.row_number",
    )

    def __repr__(self):
        return f"<ComplianceReport {self.id[:8]}: {self.marketplace} {self.filename}>"


class ComplianceReportItem(Base):
    """
    One item = one product row from the uploaded file.
    Stores per-product compliance status and issues as JSON.
    """
    __tablename__ = "compliance_report_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(
        String(36),
        ForeignKey("compliance_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    row_number = Column(Integer, nullable=False)
    sku = Column(String(500), default="")
    product_title = Column(Text, default="")

    # "compliant", "warning", "error"
    compliance_status = Column(String(20), nullable=False, default="compliant")

    # JSON array of issue dicts: [{field, rule, severity, message}, ...]
    issues = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to report
    report = relationship("ComplianceReport", back_populates="items")

    def __repr__(self):
        return f"<ComplianceReportItem row={self.row_number} sku={self.sku} status={self.compliance_status}>"
