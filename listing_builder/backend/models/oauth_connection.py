# backend/models/oauth_connection.py
# Purpose: SQLAlchemy model for per-seller OAuth connections
# NOT for: App-level API credentials or token exchange logic

from sqlalchemy import (
    Column, String, Text, DateTime, ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid


class OAuthConnection(Base):
    """Seller's OAuth connection to a marketplace (Amazon, Allegro, etc.)."""
    __tablename__ = "oauth_connections"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, nullable=False, default="default")
    marketplace = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))
    seller_id = Column(Text)
    seller_name = Column(Text)
    marketplace_ids = Column(ARRAY(Text))
    scopes = Column(Text)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
