# backend/models/team.py
# Purpose: Team workspace models — teams, members, invitations
# NOT for: Team business logic or API routes

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base
import enum


class TeamRole(str, enum.Enum):
    OWNER = "owner"      # Full control, billing, delete team
    ADMIN = "admin"      # Manage members, all data access
    EDITOR = "editor"    # Create/edit optimizations, products
    VIEWER = "viewer"    # Read-only access


class Team(Base):
    """Workspace that groups users for shared access to resources."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # WHY: Owner user_id — the person who created the team
    owner_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TeamMember(Base):
    """Links a user to a team with a specific role."""
    __tablename__ = "team_members"
    # WHY: A user can only be in a team once
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    # WHY: Store email for display — Supabase user_id is a UUID, not human-readable
    email = Column(String(255), nullable=False)
    # WHY: String not Enum — avoids CREATE TYPE conflict with migration SQL
    role = Column(String(20), nullable=False, default="editor")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class TeamInvitation(Base):
    """Pending invitation to join a team."""
    __tablename__ = "team_invitations"
    # WHY: Only one pending invite per email per team
    __table_args__ = (
        UniqueConstraint('team_id', 'email', name='uq_team_invite_email'),
    )

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    # WHY: String not Enum — avoids CREATE TYPE conflict with migration SQL
    role = Column(String(20), nullable=False, default="editor")
    # WHY: Token for email-based invite acceptance
    token = Column(String(64), unique=True, nullable=False, index=True)
    invited_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # WHY: Invites expire after 7 days
    expires_at = Column(DateTime(timezone=True), nullable=False)
