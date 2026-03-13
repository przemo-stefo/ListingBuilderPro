# backend/models/aplus_example.py
# Purpose: SQLAlchemy model for A+ Content training examples (RAG few-shot)
# NOT for: Generation logic or API routes

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class AplusTrainingExample(Base):
    """Training examples for RAG-based A+ Content generation.

    WHY: LLM gets 2-3 best examples matching category+lang as few-shot,
    improving JSON structure quality from ~27% to expected 60%+.
    """
    __tablename__ = "aplus_training_examples"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    lang = Column(String(10), nullable=False, default="pl")
    content_data = Column(JSON, nullable=False)

    # WHY: Laplace-smoothed score — starts 0.7, adjusts with feedback
    quality_score = Column(Float, default=0.7, index=True)
    times_used = Column(Integer, default=0)
    times_accepted = Column(Integer, default=0)
    times_rejected = Column(Integer, default=0)
    # WHY: Track origin — training_import vs user_generated
    source = Column(String(50), default="training_import")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
