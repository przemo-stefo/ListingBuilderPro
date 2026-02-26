# backend/models/listing.py
# Purpose: SQLAlchemy ORM models for listings and tracked keywords
# NOT for: Business logic, API routes, or compliance models

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class Listing(Base):
    """A product listing across a marketplace with compliance status."""
    __tablename__ = "listings"

    # WHY PG_UUID(as_uuid=False): Returns plain strings, matches monitoring.py pattern
    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    # WHY: Multi-tenant isolation
    user_id = Column(String(255), nullable=False, default="default", index=True)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(Text, nullable=False)
    marketplace = Column(String(50), nullable=False, index=True)
    compliance_status = Column(String(20), nullable=False, default="compliant")
    issues_count = Column(Integer, default=0)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrackedKeyword(Base):
    """A keyword being tracked for rank and search volume across a marketplace."""
    __tablename__ = "tracked_keywords"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    # WHY: Multi-tenant isolation
    user_id = Column(String(255), nullable=False, default="default", index=True)
    keyword = Column(Text, nullable=False)
    search_volume = Column(Integer, default=0)
    current_rank = Column(Integer, nullable=True)
    marketplace = Column(String(50), nullable=False, index=True)
    trend = Column(String(10), default="stable")
    relevance_score = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
