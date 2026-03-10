# backend/services/gws_client_service.py
# Purpose: Multi-tenant Google Workspace operations using client's own OAuth tokens
# NOT for: PYROX internal gws CLI (gws_office.py) or LBP reports (gws_reports.py)

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode

import httpx
import structlog
from sqlalchemy.orm import Session

from config import settings
from models.google_connection import GoogleConnection

logger = structlog.get_logger()

# WHY: Scopes needed for full office automation
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/presentations",
]


def get_authorize_url(user_id: str) -> str:
    """Generate Google OAuth2 authorization URL for popup-based flow.

    WHY: Desktop OAuth client can't redirect to external URLs.
    Popup flow with redirect_uri=postmessage works with any client type.
    Frontend opens this URL in popup, Google returns code via postMessage.
    """
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": "postmessage",
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def connect_with_code(code: str, user_id: str, db: Session) -> Optional[GoogleConnection]:
    """Exchange authorization code for tokens and store connection.

    WHY: Frontend sends code obtained from Google popup → backend exchanges for tokens.
    Uses redirect_uri=postmessage to match the authorization request.
    """
    token_data = _exchange_code(code)
    if not token_data:
        return None

    email = _get_user_email(token_data["access_token"])

    # Upsert connection
    conn = db.query(GoogleConnection).filter_by(user_id=user_id).first()
    if conn:
        conn.access_token = token_data["access_token"]
        conn.refresh_token = token_data.get("refresh_token", conn.refresh_token)
        conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
        conn.email = email
        conn.status = "active"
        conn.scopes = token_data.get("scope", "")
        conn.updated_at = datetime.now(timezone.utc)
    else:
        conn = GoogleConnection(
            user_id=user_id,
            email=email,
            status="active",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600)),
            scopes=token_data.get("scope", ""),
        )
        db.add(conn)

    db.commit()
    db.refresh(conn)
    logger.info("google_oauth_connected", user_id=user_id, email=email)
    return conn


def _exchange_code(code: str) -> Optional[dict]:
    """Exchange authorization code for access + refresh tokens."""
    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("google_token_exchange_failed", status=resp.status_code)
            return None
        return resp.json()
    except httpx.HTTPError as e:
        logger.error("google_token_exchange_error", error=str(e))
        return None


def _refresh_access_token(conn: GoogleConnection, db: Session) -> Optional[str]:
    """Refresh expired access token using refresh_token."""
    if not conn.refresh_token:
        return None

    try:
        resp = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": conn.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning("google_token_refresh_failed", status=resp.status_code)
            return None

        data = resp.json()
        conn.access_token = data["access_token"]
        conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
        conn.updated_at = datetime.now(timezone.utc)
        db.commit()
        return data["access_token"]
    except httpx.HTTPError as e:
        logger.error("google_token_refresh_error", error=str(e))
        return None


def _get_valid_token(user_id: str, db: Session) -> Optional[str]:
    """Get valid access token for user, refreshing if needed."""
    conn = db.query(GoogleConnection).filter_by(user_id=user_id, status="active").first()
    if not conn:
        return None

    # WHY: 5-minute buffer — refresh before expiry to avoid mid-request failures
    if conn.token_expires_at and conn.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
        return _refresh_access_token(conn, db)

    return conn.access_token


def _get_user_email(access_token: str) -> Optional[str]:
    """Get Google account email from access token."""
    try:
        resp = httpx.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        return resp.json().get("email") if resp.status_code == 200 else None
    except httpx.HTTPError:
        return None


def _google_api(method: str, url: str, token: str, json_data: dict = None, params: dict = None) -> dict:
    """Make authenticated Google API request.

    WHY: Direct REST API calls with client's token — no gws CLI needed per client.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = httpx.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = httpx.post(url, headers=headers, json=json_data, timeout=30)
        elif method == "PUT":
            resp = httpx.put(url, headers=headers, json=json_data, timeout=30)
        elif method == "DELETE":
            resp = httpx.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}

        if resp.status_code >= 400:
            return {"error": resp.text[:500], "status": resp.status_code}
        return resp.json() if resp.text.strip() else {}
    except httpx.HTTPError as e:
        return {"error": str(e)}


# ─── Client-facing Google Workspace operations ──────────────────────────────

def client_send_email(user_id: str, db: Session, to: str, subject: str, body: str) -> dict:
    """Send email via client's Gmail."""
    token = _get_valid_token(user_id, db)
    if not token:
        return {"error": "Google nie podlaczony. Autoryzuj najpierw."}

    import base64
    message = f"To: {to}\r\nSubject: {subject}\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{body}"
    raw = base64.urlsafe_b64encode(message.encode()).decode()

    return _google_api(
        "POST", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        token, json_data={"raw": raw},
    )


def client_list_drive_files(user_id: str, db: Session, query: str = "", max_results: int = 10) -> dict:
    """List files on client's Google Drive."""
    token = _get_valid_token(user_id, db)
    if not token:
        return {"error": "Google nie podlaczony."}

    params = {
        "pageSize": min(max_results, 50),
        "orderBy": "modifiedTime desc",
        "fields": "files(id,name,mimeType,modifiedTime,size)",
    }
    if query:
        params["q"] = query

    return _google_api("GET", "https://www.googleapis.com/drive/v3/files", token, params=params)


def client_create_sheet(user_id: str, db: Session, title: str, data: List[List] = None) -> dict:
    """Create a Google Sheet on client's account."""
    token = _get_valid_token(user_id, db)
    if not token:
        return {"error": "Google nie podlaczony."}

    result = _google_api(
        "POST", "https://sheets.googleapis.com/v4/spreadsheets",
        token, json_data={"properties": {"title": title}},
    )

    if "error" in result:
        return result

    spreadsheet_id = result.get("spreadsheetId")
    if data and spreadsheet_id:
        _google_api(
            "PUT",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Sheet1!A1",
            token,
            json_data={"values": data},
            params={"valueInputOption": "USER_ENTERED"},
        )

    return result


def client_create_calendar_event(
    user_id: str, db: Session, summary: str, start: str, end: str,
    description: str = "", attendees: List[str] = None, tz: str = "Europe/Warsaw",
) -> dict:
    """Create a calendar event on client's Google Calendar."""
    token = _get_valid_token(user_id, db)
    if not token:
        return {"error": "Google nie podlaczony."}

    event = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": tz},
        "end": {"dateTime": end, "timeZone": tz},
    }
    if description:
        event["description"] = description
    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    return _google_api(
        "POST", "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        token, json_data=event,
    )
