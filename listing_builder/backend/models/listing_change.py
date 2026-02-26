# backend/models/listing_change.py
# Purpose: SQLAlchemy ORM model for field-level listing changes
# NOT for: Diff logic (listing_diff_service) or API routes

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class ListingChange(Base):
    """A single detected change in a listing field (title, bullets, images, etc.)."""
    __tablename__ = "listing_changes"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tracked_product_id = Column(
        PG_UUID(as_uuid=False),
        ForeignKey("tracked_products.id", ondelete="CASCADE"),
        index=True,
    )
    user_id = Column(Text, nullable=False, index=True)
    marketplace = Column(String(50), nullable=False)
    product_id = Column(String(500), nullable=False)
    # WHY change_type: Groups changes by field category (title/bullets/description/images/price/brand)
    change_type = Column(String(50), nullable=False)
    # WHY field_name: Sub-field detail (e.g. "bullet_2", "image_main", price % change)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
