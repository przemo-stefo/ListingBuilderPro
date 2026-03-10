# backend/api/office_routes.py
# Purpose: PYROX AI office automation endpoints — Docs templates, invoices, calendar
# NOT for: LBP reports (report_routes.py) or client-facing features

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
import asyncio
import structlog

from api.dependencies import require_user_id
from services.gws_office import (
    create_drip_template, read_drip_template, list_drip_templates,
    create_invoice_sheet, list_invoices,
    create_calendar_event, list_upcoming_events, delete_calendar_event,
)

limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

router = APIRouter(prefix="/api/office", tags=["Office"])


# ─── Drip Templates (Google Docs) ───────────────────────────────────────────

class DripTemplateRequest(BaseModel):
    template_name: str = Field(..., min_length=3, max_length=200)
    subject: str = Field(..., min_length=3, max_length=300)
    html_body: str = Field(..., min_length=10, max_length=50000)
    variables: List[str] = Field(default_factory=list)


@router.post("/templates")
@limiter.limit("5/minute")
async def create_template(
    request: Request, body: DripTemplateRequest,
    user_id: str = Depends(require_user_id),
):
    """Create a drip campaign email template as a Google Doc."""
    doc_id = await asyncio.to_thread(
        create_drip_template, body.template_name, body.subject, body.html_body, body.variables,
    )
    if not doc_id:
        raise HTTPException(status_code=503, detail="Nie udalo sie utworzyc szablonu.")
    url = f"https://docs.google.com/document/d/{doc_id}"
    return {"status": "ok", "document_id": doc_id, "url": url}


@router.get("/templates")
@limiter.limit("10/minute")
async def get_templates(request: Request, user_id: str = Depends(require_user_id)):
    """List all drip campaign templates."""
    templates = await asyncio.to_thread(list_drip_templates)
    return {"status": "ok", "templates": templates}


@router.get("/templates/{doc_id}")
@limiter.limit("10/minute")
async def get_template_content(
    request: Request, doc_id: str, user_id: str = Depends(require_user_id),
):
    """Read a drip template content from Google Docs."""
    content = await asyncio.to_thread(read_drip_template, doc_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Szablon nie znaleziony.")
    return {"status": "ok", "content": content}


# ─── Invoices (Google Sheets) ────────────────────────────────────────────────

class InvoiceItem(BaseModel):
    description: str = Field(..., min_length=3, max_length=500)
    quantity: float = Field(..., gt=0)
    rate: float = Field(..., gt=0)


class InvoiceRequest(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    client_name: str = Field(..., min_length=2, max_length=200)
    client_address: str = Field(default="", max_length=500)
    client_nip: str = Field(default="", max_length=20)
    items: List[InvoiceItem] = Field(..., min_length=1, max_length=20)
    currency: str = Field(default="USD", max_length=5)
    notes: str = Field(default="", max_length=2000)


@router.post("/invoices")
@limiter.limit("5/minute")
async def create_invoice(
    request: Request, body: InvoiceRequest,
    user_id: str = Depends(require_user_id),
):
    """Generate an invoice as a Google Sheet."""
    items_dicts = [item.model_dump() for item in body.items]
    spreadsheet_id = await asyncio.to_thread(
        create_invoice_sheet, body.invoice_number, body.client_name,
        body.client_address, body.client_nip, items_dicts, body.currency, body.notes,
    )
    if not spreadsheet_id:
        raise HTTPException(status_code=503, detail="Nie udalo sie utworzyc faktury.")
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    total = sum(i.quantity * i.rate for i in body.items)
    return {"status": "ok", "spreadsheet_id": spreadsheet_id, "url": url, "total": total}


@router.get("/invoices")
@limiter.limit("10/minute")
async def get_invoices(request: Request, user_id: str = Depends(require_user_id)):
    """List all invoices from Google Drive."""
    invoices = await asyncio.to_thread(list_invoices)
    return {"status": "ok", "invoices": invoices}


# ─── Calendar (Google Calendar) ──────────────────────────────────────────────

class CalendarEventRequest(BaseModel):
    summary: str = Field(..., min_length=3, max_length=300)
    start: str = Field(..., description="ISO 8601 datetime")
    end: str = Field(..., description="ISO 8601 datetime")
    description: str = Field(default="", max_length=5000)
    attendees: List[str] = Field(default_factory=list, max_length=20)
    timezone: str = Field(default="Europe/Warsaw", max_length=50)


@router.post("/calendar")
@limiter.limit("10/minute")
async def create_event(
    request: Request, body: CalendarEventRequest,
    user_id: str = Depends(require_user_id),
):
    """Create a Google Calendar event."""
    event_id = await asyncio.to_thread(
        create_calendar_event, body.summary, body.start, body.end,
        body.description, body.attendees, body.timezone,
    )
    if not event_id:
        raise HTTPException(status_code=503, detail="Nie udalo sie utworzyc wydarzenia.")
    return {"status": "ok", "event_id": event_id}


@router.get("/calendar")
@limiter.limit("10/minute")
async def get_events(
    request: Request,
    max_results: int = 10,
    user_id: str = Depends(require_user_id),
):
    """List upcoming Google Calendar events."""
    events = await asyncio.to_thread(list_upcoming_events, min(max_results, 50))
    return {"status": "ok", "events": events}


@router.delete("/calendar/{event_id}")
@limiter.limit("5/minute")
async def remove_event(
    request: Request, event_id: str,
    user_id: str = Depends(require_user_id),
):
    """Delete a Google Calendar event."""
    success = await asyncio.to_thread(delete_calendar_event, event_id)
    if not success:
        raise HTTPException(status_code=503, detail="Nie udalo sie usunac wydarzenia.")
    return {"status": "ok"}
