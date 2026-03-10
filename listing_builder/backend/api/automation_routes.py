# backend/api/automation_routes.py
# Purpose: Client-facing AI Office Automation endpoints — Google Workspace via client's OAuth
# NOT for: PYROX internal office (office_routes.py) or LBP reports (report_routes.py)

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
import asyncio
import structlog

from database import get_db
from api.dependencies import require_user_id
from services.gws_client_service import (
    get_authorize_url, connect_with_code,
    client_send_email, client_list_drive_files,
    client_create_sheet, client_create_calendar_event,
)
from models.google_connection import GoogleConnection

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/automation", tags=["AI Office Automation"])


# ─── Google OAuth connection (popup-based flow) ─────────────────────────────

@router.get("/google/authorize")
@limiter.limit("5/minute")
async def google_authorize(
    request: Request,
    user_id: str = Depends(require_user_id),
):
    """Generate Google OAuth URL for popup-based authorization.

    WHY: Popup flow with redirect_uri=postmessage works with Desktop OAuth clients.
    No need for registered redirect URIs. Frontend opens popup, gets code via postMessage.
    """
    url = get_authorize_url(user_id)
    return {"status": "ok", "authorize_url": url, "client_id": settings.google_oauth_client_id}


class GoogleConnectRequest(BaseModel):
    code: str = Field(..., min_length=10, max_length=500)


@router.post("/google/connect")
@limiter.limit("5/minute")
async def google_connect(
    request: Request,
    body: GoogleConnectRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Exchange Google authorization code for tokens and store connection.

    WHY: Frontend sends code from Google popup → backend exchanges for tokens.
    Two-step flow: 1) GET /authorize → URL, 2) POST /connect → {code}.
    """
    conn = connect_with_code(body.code, user_id, db)
    if not conn:
        raise HTTPException(status_code=400, detail="Nie udalo sie polaczyc z Google. Sprobuj ponownie.")
    return {
        "status": "ok",
        "email": conn.email,
        "scopes": conn.scopes,
    }


@router.get("/google/status")
@limiter.limit("10/minute")
async def google_status(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Check if client has an active Google connection."""
    conn = db.query(GoogleConnection).filter_by(user_id=user_id, status="active").first()
    if not conn:
        return {"status": "not_connected"}
    return {
        "status": "connected",
        "email": conn.email,
        "scopes": conn.scopes,
        "connected_at": str(conn.created_at),
    }


@router.delete("/google/disconnect")
@limiter.limit("3/minute")
async def google_disconnect(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Revoke Google connection."""
    conn = db.query(GoogleConnection).filter_by(user_id=user_id, status="active").first()
    if not conn:
        raise HTTPException(status_code=404, detail="Brak aktywnego polaczenia Google.")
    conn.status = "revoked"
    db.commit()
    return {"status": "ok"}


# ─── Gmail ───────────────────────────────────────────────────────────────────

class SendEmailRequest(BaseModel):
    to: str = Field(..., min_length=5, max_length=200)
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=50000)


@router.post("/gmail/send")
@limiter.limit("10/minute")
async def send_email(
    request: Request, body: SendEmailRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Send email via client's Gmail account."""
    result = await asyncio.to_thread(client_send_email, user_id, db, body.to, body.subject, body.body)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return {"status": "ok", "message_id": result.get("id")}


# ─── Drive ───────────────────────────────────────────────────────────────────

@router.get("/drive/files")
@limiter.limit("10/minute")
async def list_files(
    request: Request,
    q: str = Query("", max_length=500),
    max_results: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """List files on client's Google Drive."""
    result = await asyncio.to_thread(client_list_drive_files, user_id, db, q, max_results)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return {"status": "ok", "files": result.get("files", [])}


# ─── Sheets ──────────────────────────────────────────────────────────────────

class CreateSheetRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    data: Optional[List[List]] = Field(None, description="Initial data rows")


@router.post("/sheets/create")
@limiter.limit("5/minute")
async def create_sheet(
    request: Request, body: CreateSheetRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Create a Google Sheet on client's account."""
    result = await asyncio.to_thread(client_create_sheet, user_id, db, body.title, body.data)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    sid = result.get("spreadsheetId")
    return {"status": "ok", "spreadsheet_id": sid, "url": f"https://docs.google.com/spreadsheets/d/{sid}"}


# ─── Calendar ────────────────────────────────────────────────────────────────

class CreateEventRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=300)
    start: str = Field(..., description="ISO 8601 datetime")
    end: str = Field(..., description="ISO 8601 datetime")
    description: str = Field(default="", max_length=5000)
    attendees: List[str] = Field(default_factory=list, max_length=20)
    timezone: str = Field(default="Europe/Warsaw", max_length=50)


@router.post("/calendar/event")
@limiter.limit("10/minute")
async def create_event(
    request: Request, body: CreateEventRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    """Create event on client's Google Calendar."""
    result = await asyncio.to_thread(
        client_create_calendar_event, user_id, db, body.summary,
        body.start, body.end, body.description, body.attendees, body.timezone,
    )
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return {"status": "ok", "event_id": result.get("id")}


# WHY: Import settings here (not top-level) to avoid circular import at module load
from config import settings
