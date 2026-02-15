# backend/models/premium_license.py
# Purpose: SQLAlchemy ORM model for license-key based premium access
# NOT for: Subscription billing (that's subscription.py)

from sqlalchemy import Column, String, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
import uuid


from database import Base


class PremiumLicense(Base):
    """One license key per Stripe checkout — validates premium access."""
    __tablename__ = "premium_licenses"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(Text, nullable=False)
    license_key = Column(Text, nullable=False, unique=True)
    stripe_customer_id = Column(Text)
    stripe_checkout_session_id = Column(Text, unique=True)
    stripe_subscription_id = Column(Text)
    plan_type = Column(Text, nullable=False)  # monthly
    status = Column(Text, nullable=False, default="active")  # active | revoked | expired
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
