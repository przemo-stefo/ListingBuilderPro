# backend/models/shared_listing.py
# Purpose: Stores shared listing snapshots with public access tokens
# NOT for: Optimization logic or user auth

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class SharedListing(Base):
    """Public snapshot of an optimized listing — accessible via unique token."""
    __tablename__ = "shared_listings"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    product_title = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=False)
    marketplace = Column(String(50), nullable=False)
    # WHY: Store full listing + scores snapshot — immutable public view
    listing_data = Column(JSON, nullable=False)
    scores_data = Column(JSON)
    compliance_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # WHY: Optional expiry — None means never expires
    expires_at = Column(DateTime(timezone=True), nullable=True)
