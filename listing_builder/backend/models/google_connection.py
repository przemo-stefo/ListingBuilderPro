# backend/models/google_connection.py
# Purpose: SQLAlchemy model for client Google Workspace OAuth connections
# NOT for: PYROX internal gws CLI usage (that's gws_office.py) or marketplace OAuth (oauth_connection.py)

from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class GoogleConnection(Base):
    """Client's Google Workspace OAuth connection for AI Office Automation.

    WHY separate from OAuthConnection: Marketplace OAuth has seller_id, marketplace_ids, etc.
    Google Workspace OAuth has scopes, email, and different token lifecycle.
    """
    __tablename__ = "google_connections"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, nullable=False)
    email = Column(Text)  # Google account email
    status = Column(Text, nullable=False, default="pending")  # pending | active | revoked
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))
    scopes = Column(Text)  # Space-separated OAuth scopes granted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
