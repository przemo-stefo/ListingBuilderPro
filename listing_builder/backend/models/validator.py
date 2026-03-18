# backend/models/validator.py
# Purpose: SQLAlchemy model for product validation runs
# NOT for: Business logic (that's validator_service.py)

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from database import Base


class ValidationRun(Base):
    """Single product validation analysis result."""

    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, default="default", index=True)
    product_input = Column(String(500), nullable=False)
    input_type = Column(String(20), nullable=False)  # 'name' | 'asin' | 'url'
    marketplace = Column(String(50), default="amazon")
    trends_data = Column(JSON, nullable=True)
    competition_data = Column(JSON, nullable=True)
    score = Column(Integer, nullable=False)
    verdict = Column(String(20), nullable=False)  # 'warto' | 'ryzykowne' | 'odpusc'
    explanation = Column(Text, nullable=False)
    dimensions = Column(JSON, nullable=False)
    provider_used = Column(String(30), default="beast")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    client_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
