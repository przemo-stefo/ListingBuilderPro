# backend/models/attribute_run.py
# Purpose: SQLAlchemy model for attribute generation runs
# NOT for: Business logic (that's attribute_service.py)

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from database import Base


class AttributeRun(Base):
    """Single attribute generation result."""

    __tablename__ = "attribute_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, default="default", index=True)
    product_input = Column(String(500), nullable=False)
    marketplace = Column(String(50), default="allegro")
    category_id = Column(String(50), nullable=True)
    category_name = Column(String(255), nullable=True)
    category_path = Column(Text, nullable=True)
    attributes = Column(JSON, nullable=False)
    params_count = Column(Integer, default=0)
    provider_used = Column(String(30), default="beast")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    client_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
