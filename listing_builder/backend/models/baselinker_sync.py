# backend/models/baselinker_sync.py
# Purpose: Sync log for BOL.com → BaseLinker order transfer
# NOT for: BOL.com API calls or BaseLinker business logic

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from database import Base


class BaseLinkerSyncLog(Base):
    """One row per BOL order synced (or failed) to BaseLinker."""
    __tablename__ = "baselinker_sync_log"

    id = Column(Integer, primary_key=True)
    bol_order_id = Column(String(50), unique=True, index=True, nullable=False)
    baselinker_order_id = Column(String(50))  # WHY: ID returned by BaseLinker addOrder
    status = Column(String(20), nullable=False)  # "synced" | "error"
    error_message = Column(Text)
    bol_order_data = Column(JSON)  # WHY: Raw BOL data for debugging
    created_at = Column(DateTime(timezone=True), server_default=func.now())
