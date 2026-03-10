# backend/api/team_routes.py
# Purpose: Team workspace API — CRUD, invitations, member management
# NOT for: Team-scoped resource queries (those stay in their own routes)

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from database import get_db
from api.dependencies import require_user_id, require_premium
from models.team import Team, TeamMember, TeamInvitation, TeamRole

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/teams", tags=["teams"])


# --- Schemas ---

class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class UpdateTeamRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class InviteMemberRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    role: TeamRole = TeamRole.EDITOR

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("role")
    @classmethod
    def no_owner_invite(cls, v: TeamRole) -> TeamRole:
        if v == TeamRole.OWNER:
            raise ValueError("Cannot invite as owner")
        return v


class AcceptInvitationRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=30)


class UpdateMemberRoleRequest(BaseModel):
    role: TeamRole

    @field_validator("role")
    @classmethod
    def no_owner_assign(cls, v: TeamRole) -> TeamRole:
        if v == TeamRole.OWNER:
            raise ValueError("Cannot assign owner role")
        return v


class TeamResponse(BaseModel):
    id: int
    name: str
    owner_id: str
    member_count: int
    my_role: str
    created_at: datetime


class MemberResponse(BaseModel):
    id: int
    user_id: str
    email: str
    role: str
    joined_at: datetime


class InvitationResponse(BaseModel):
    id: int
    email: str
    role: str
    token: str
    invited_by: str
    created_at: datetime
    expires_at: datetime


# --- Helpers ---

def _get_membership(db: Session, team_id: int, user_id: str) -> TeamMember:
    """Get user's membership in a team, raise 404 if not found."""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team not found or you are not a member")
    return member


def _require_role(member: TeamMember, min_roles: list[TeamRole]):
    """Check if member has one of the required roles."""
    if TeamRole(member.role) not in min_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


# --- Team CRUD ---

@router.post("", status_code=201)
@limiter.limit("5/minute")
async def create_team(
    request: Request,
    body: CreateTeamRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Create a new team. Creator becomes owner. Premium only."""
    require_premium(request, db)

    # WHY: Limit teams per user to prevent abuse
    existing = db.query(Team).filter(Team.owner_id == user_id).count()
    if existing >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 teams per user")

    # WHY: Need email from JWT for member record
    email = getattr(request.state, "user_email", user_id[:20] + "@unknown")

    team = Team(name=body.name, owner_id=user_id)
    db.add(team)
    db.flush()  # WHY: Get team.id before creating member

    owner_member = TeamMember(
        team_id=team.id,
        user_id=user_id,
        email=email,
        role=TeamRole.OWNER,
    )
    db.add(owner_member)
    db.commit()

    logger.info("team_created", team_id=team.id, owner=user_id[:8])
    return {"id": team.id, "name": team.name}


# WHY: Must be defined BEFORE /{team_id} routes — FastAPI matches routes in order
@router.post("/accept-invitation")
@limiter.limit("10/minute")
async def accept_invitation(
    request: Request,
    body: Optional[AcceptInvitationRequest] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Accept an invitation by token. Token from query param or JSON body."""
    token = request.query_params.get("token", "")
    if not token and body:
        token = body.token

    if not token or len(token) < 10 or len(token) > 30:
        raise HTTPException(status_code=400, detail="Invalid invitation token")

    invite = db.query(TeamInvitation).filter(TeamInvitation.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")

    if invite.expires_at < datetime.now(timezone.utc):
        db.delete(invite)
        db.commit()
        raise HTTPException(status_code=410, detail="Invitation has expired")

    # WHY: Race condition guard
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == invite.team_id, TeamMember.user_id == user_id
    ).first()
    if existing:
        db.delete(invite)
        db.commit()
        raise HTTPException(status_code=400, detail="You are already a member of this team")

    email = getattr(request.state, "user_email", invite.email)
    member = TeamMember(
        team_id=invite.team_id,
        user_id=user_id,
        email=email,
        role=invite.role,
    )
    db.add(member)
    db.delete(invite)
    db.commit()

    team = db.query(Team).filter(Team.id == invite.team_id).first()
    logger.info("invitation_accepted", team_id=invite.team_id, user=user_id[:8])
    return {"team_id": team.id, "team_name": team.name, "role": invite.role}


@router.get("")
async def list_my_teams(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List all teams the user belongs to."""
    memberships = db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
    if not memberships:
        return []

    team_ids = [m.team_id for m in memberships]
    role_map = {m.team_id: m.role for m in memberships}

    # WHY: Single query with subquery count — avoids N+1
    count_sub = (
        db.query(TeamMember.team_id, sa_func.count(TeamMember.id).label("cnt"))
        .filter(TeamMember.team_id.in_(team_ids))
        .group_by(TeamMember.team_id)
        .subquery()
    )
    teams = db.query(Team, count_sub.c.cnt).outerjoin(
        count_sub, Team.id == count_sub.c.team_id
    ).filter(Team.id.in_(team_ids)).all()

    return [
        TeamResponse(
            id=t.id, name=t.name, owner_id=t.owner_id,
            member_count=cnt or 0, my_role=role_map[t.id],
            created_at=t.created_at,
        )
        for t, cnt in teams
    ]


@router.get("/{team_id}")
async def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Get team details. Must be a member."""
    member = _get_membership(db, team_id, user_id)
    team = db.query(Team).filter(Team.id == team_id).first()
    count = db.query(TeamMember).filter(TeamMember.team_id == team_id).count()
    return TeamResponse(
        id=team.id, name=team.name, owner_id=team.owner_id,
        member_count=count, my_role=member.role,
        created_at=team.created_at,
    )


@router.patch("/{team_id}")
async def update_team(
    team_id: int,
    body: UpdateTeamRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Rename team. Owner/admin only."""
    member = _get_membership(db, team_id, user_id)
    _require_role(member, [TeamRole.OWNER, TeamRole.ADMIN])

    team = db.query(Team).filter(Team.id == team_id).first()
    team.name = body.name
    db.commit()
    return {"ok": True}


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Delete team. Owner only. Cascades to members and invitations."""
    member = _get_membership(db, team_id, user_id)
    _require_role(member, [TeamRole.OWNER])

    db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id).delete()
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
    db.query(Team).filter(Team.id == team_id).delete()
    db.commit()
    logger.info("team_deleted", team_id=team_id, by=user_id[:8])


# --- Members ---

@router.get("/{team_id}/members")
async def list_members(
    team_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List team members. Any member can view."""
    _get_membership(db, team_id, user_id)
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return [
        MemberResponse(id=m.id, user_id=m.user_id, email=m.email, role=m.role, joined_at=m.joined_at)
        for m in members
    ]


@router.patch("/{team_id}/members/{member_id}")
async def update_member_role(
    team_id: int,
    member_id: int,
    body: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Change a member's role. Owner/admin only. Cannot change owner."""
    actor = _get_membership(db, team_id, user_id)
    _require_role(actor, [TeamRole.OWNER, TeamRole.ADMIN])

    target = db.query(TeamMember).filter(
        TeamMember.id == member_id, TeamMember.team_id == team_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    if TeamRole(target.role) == TeamRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot change owner's role")

    target.role = body.role
    db.commit()
    return {"ok": True}


@router.delete("/{team_id}/members/{member_id}", status_code=204)
async def remove_member(
    team_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Remove a member. Owner/admin, or self-remove. Cannot remove owner."""
    actor = _get_membership(db, team_id, user_id)
    target = db.query(TeamMember).filter(
        TeamMember.id == member_id, TeamMember.team_id == team_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    if TeamRole(target.role) == TeamRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")

    # WHY: Allow self-removal (leaving team) or admin action
    is_self = target.user_id == user_id
    if not is_self:
        _require_role(actor, [TeamRole.OWNER, TeamRole.ADMIN])

    db.delete(target)
    db.commit()
    logger.info("member_removed", team_id=team_id, removed=target.user_id[:8], by=user_id[:8])


# --- Invitations ---

@router.post("/{team_id}/invitations", status_code=201)
@limiter.limit("10/minute")
async def create_invitation(
    request: Request,
    team_id: int,
    body: InviteMemberRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Invite a user by email. Owner/admin only."""
    actor = _get_membership(db, team_id, user_id)
    _require_role(actor, [TeamRole.OWNER, TeamRole.ADMIN])

    # WHY: Check if already a member
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.email == body.email
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a team member")

    # WHY: Check for existing pending invite
    existing_invite = db.query(TeamInvitation).filter(
        TeamInvitation.team_id == team_id, TeamInvitation.email == body.email
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invitation already pending for this email")

    invite = TeamInvitation(
        team_id=team_id,
        email=body.email,
        role=body.role,
        token=secrets.token_urlsafe(16),
        invited_by=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    logger.info("invitation_created", team_id=team_id, email=body.email, by=user_id[:8])
    return {"token": invite.token, "expires_at": invite.expires_at.isoformat()}


@router.get("/{team_id}/invitations")
async def list_invitations(
    team_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List pending invitations. Owner/admin only."""
    actor = _get_membership(db, team_id, user_id)
    _require_role(actor, [TeamRole.OWNER, TeamRole.ADMIN])

    invites = db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id).all()
    return [
        InvitationResponse(
            id=i.id, email=i.email, role=i.role, token=i.token,
            invited_by=i.invited_by, created_at=i.created_at, expires_at=i.expires_at,
        )
        for i in invites
    ]


@router.delete("/{team_id}/invitations/{invitation_id}", status_code=204)
async def revoke_invitation(
    team_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Revoke a pending invitation. Owner/admin only."""
    actor = _get_membership(db, team_id, user_id)
    _require_role(actor, [TeamRole.OWNER, TeamRole.ADMIN])

    invite = db.query(TeamInvitation).filter(
        TeamInvitation.id == invitation_id, TeamInvitation.team_id == team_id
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")

    db.delete(invite)
    db.commit()
