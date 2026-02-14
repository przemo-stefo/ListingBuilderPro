# backend/models/epr_country.py
# Purpose: SQLAlchemy model for per-country EPR rules (packaging, WEEE, batteries)
# NOT for: Actual EPR report data from SP-API (that's epr.py)

from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class EprCountryRule(Base):
    """Per-country EPR regulation rule with thresholds, deadlines, registration links."""
    __tablename__ = "epr_country_rules"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(Text, nullable=False)
    country_name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    registration_required = Column(Boolean, nullable=False, default=True)
    authority_name = Column(Text)
    authority_url = Column(Text)
    threshold_description = Column(Text)
    threshold_units = Column(Integer)
    threshold_revenue_eur = Column(Integer)
    deadline = Column(Text)
    penalty_description = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
