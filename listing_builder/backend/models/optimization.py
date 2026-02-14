# backend/models/optimization.py
# Purpose: Stores completed optimization runs for history/reload
# NOT for: Request validation or LLM logic

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class OptimizationRun(Base):
    """One saved optimization result — request + full response stored as JSON."""
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    product_title = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=False)
    marketplace = Column(String(50), nullable=False)
    mode = Column(String(20), nullable=False)
    coverage_pct = Column(Float, default=0)
    compliance_status = Column(String(20), default="UNKNOWN")
    request_data = Column(JSON)  # WHY: Full request for re-running
    response_data = Column(JSON)  # WHY: Full response for reload
    trace_data = Column(JSON)  # WHY: Observability — tokens, latency, cost per run
    client_ip = Column(String(45))  # WHY: Per-IP free tier limit enforcement
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OptimizationRun {self.id}: {self.product_title[:30]}>"
