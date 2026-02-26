# backend/models/epr.py
# Purpose: SQLAlchemy ORM models for EPR (Extended Producer Responsibility) reports
# NOT for: SP-API communication or report parsing logic

from sqlalchemy import (
    Column, String, Integer, Numeric, Text, DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class EprReport(Base):
    """An EPR report fetched from Amazon SP-API."""
    __tablename__ = "epr_reports"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    # WHY: Multi-tenant isolation
    user_id = Column(String(255), nullable=False, default="default", index=True)
    report_type = Column(Text, nullable=False)
    marketplace_id = Column(Text, nullable=False, default="A1PA6795UKMFR9")
    status = Column(Text, nullable=False, default="pending")
    sp_api_report_id = Column(Text)
    row_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    rows = relationship(
        "EprReportRow",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="EprReportRow.asin",
    )


class EprReportRow(Base):
    """A single row (ASIN) within an EPR report."""
    __tablename__ = "epr_report_rows"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(
        PG_UUID(as_uuid=False),
        ForeignKey("epr_reports.id", ondelete="CASCADE"),
        index=True,
    )
    asin = Column(Text)
    marketplace = Column(Text)
    epr_category = Column(Text)
    registration_number = Column(Text)
    paper_kg = Column(Numeric(10, 4), default=0)
    glass_kg = Column(Numeric(10, 4), default=0)
    aluminum_kg = Column(Numeric(10, 4), default=0)
    steel_kg = Column(Numeric(10, 4), default=0)
    plastic_kg = Column(Numeric(10, 4), default=0)
    wood_kg = Column(Numeric(10, 4), default=0)
    units_sold = Column(Integer, default=0)
    reporting_period = Column(Text)

    report = relationship("EprReport", back_populates="rows")
