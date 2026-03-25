# backend/models/catalog_health.py
# Purpose: SQLAlchemy models for Catalog Health Check scan + issues
# NOT for: Business logic (catalog_health_service.py) or API routes

from sqlalchemy import Column, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class CatalogScan(Base):
    __tablename__ = "catalog_scans"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(Text, nullable=False, index=True)
    marketplace = Column(Text, nullable=False, server_default="DE")
    seller_id = Column(Text)
    status = Column(Text, nullable=False, server_default="pending")  # pending, scanning, completed, failed
    progress = Column(JSONB, server_default='{"phase": "waiting", "percent": 0}')
    total_listings = Column(Integer, server_default="0")
    issues_found = Column(Integer, server_default="0")
    issues_fixed = Column(Integer, server_default="0")
    scan_data = Column(JSONB, server_default="{}")  # Raw report data cache
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    issues = relationship("CatalogIssue", back_populates="scan", cascade="all, delete-orphan")


class CatalogIssue(Base):
    __tablename__ = "catalog_issues"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    scan_id = Column(PG_UUID(as_uuid=False), ForeignKey("catalog_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    asin = Column(Text)
    sku = Column(Text)
    issue_type = Column(Text, nullable=False, index=True)  # broken_variation, missing_attribute, suppressed_listing, stranded_inventory, orphaned_asin, low_quality_image, invalid_price
    severity = Column(Text, nullable=False, server_default="warning", index=True)  # critical, warning, info
    title = Column(Text, nullable=False)
    description = Column(Text)
    amazon_issue_code = Column(Text)  # From SP-API issues array
    fix_proposal = Column(JSONB)  # {"action": "patch", "sku": "X", "patches": [...]}
    fix_status = Column(Text, server_default="pending")  # pending, applied, failed, skipped
    fix_result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("CatalogScan", back_populates="issues")
