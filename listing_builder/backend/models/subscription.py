# backend/models/subscription.py
# Purpose: SQLAlchemy ORM model for Stripe subscriptions
# NOT for: Payment processing or Stripe API calls

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class Subscription(Base):
    """Tracks Stripe subscription state per user."""
    __tablename__ = "subscriptions"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, nullable=False, default="default", unique=True)
    stripe_customer_id = Column(Text)
    stripe_subscription_id = Column(Text)
    stripe_price_id = Column(Text)
    status = Column(Text, nullable=False, default="inactive")  # active/past_due/canceled/inactive
    tier = Column(Text, nullable=False, default="free")  # free/premium
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
