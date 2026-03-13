# backend/services/gws_office.py
# Purpose: PYROX AI office automation via REST API — Docs templates, Sheets invoices, Calendar events
# NOT for: LBP reports (gws_reports.py) or client OAuth (gws_client_service.py)

from __future__ import annotations

import base64
from datetime import datetime
from typing import Dict, List, Optional

import structlog

from services.gws_auth import google_api

logger = structlog.get_logger()

DOCS_API = "https://docs.googleapis.com/v1/documents"
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE_API = "https://www.googleapis.com/drive/v3"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"


# ─── GOOGLE DOCS: Drip campaign templates ───────────────────────────────────

def create_drip_template(
    template_name: str,
    subject: str,
    html_body: str,
    variables: List[str],
) -> Optional[str]:
    """Create a Google Doc as an email template with merge variables.

    WHY: Google Docs = versionable, team-editable, shareable. Replaces hardcoded
    n8n HTML strings. Variables like {{name}}, {{company}} are preserved as-is.
    Returns document ID or None on failure.
    """
    result = google_api("POST", DOCS_API, json_data={"title": f"[Drip] {template_name}"})

    doc_id = result.get("documentId")
    if not doc_id:
        logger.error("doc_create_failed", template=template_name, error=result)
        return None

    # WHY: Insert content after creation — Docs API requires batchUpdate for content
    content = (
        f"SZABLON EMAIL: {template_name}\n"
        f"Temat: {subject}\n"
        f"Zmienne: {', '.join(variables)}\n"
        f"---\n\n"
        f"{html_body}"
    )
    google_api("POST", f"{DOCS_API}/{doc_id}:batchUpdate", json_data={
        "requests": [{"insertText": {"location": {"index": 1}, "text": content}}],
    })

    logger.info("doc_created", id=doc_id, template=template_name)
    return doc_id


def read_drip_template(doc_id: str) -> Optional[str]:
    """Read a Google Doc template content.

    WHY: n8n Code node can fetch template from Docs before sending email.
    """
    result = google_api("GET", f"{DOCS_API}/{doc_id}")

    if "error" in result:
        return None

    body = result.get("body", {})
    content = body.get("content", [])
    text_parts = []
    for element in content:
        for para_elem in element.get("paragraph", {}).get("elements", []):
            text_run = para_elem.get("textRun", {})
            if "content" in text_run:
                text_parts.append(text_run["content"])

    full_text = "".join(text_parts)
    if "---\n\n" in full_text:
        return full_text.split("---\n\n", 1)[1]
    return full_text


def list_drip_templates() -> List[Dict]:
    """List all drip campaign templates from Drive."""
    result = google_api("GET", f"{DRIVE_API}/files", params={
        "q": "name contains '[Drip]' and mimeType = 'application/vnd.google-apps.document'",
        "fields": "files(id,name,modifiedTime)",
        "orderBy": "modifiedTime desc",
    })
    files = result.get("files", [])
    return [{"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", "")} for f in files]


# ─── GOOGLE SHEETS: Invoice generation ──────────────────────────────────────

PYROX_COMPANY = {
    "name": "PYROX AI, LLC",
    "address": "1060 Everett Lane, Des Plaines, IL 60018",
    "ein": "41-3665972",
    "email": "robskorupski@pyroxai.com",
    "bank_domestic": "ABA 021000021 | Acct 2907521671",
    "bank_swift": "CHASUS33 | Acct 2907521671",
    "terms": "Net 30",
}


def create_invoice_sheet(
    invoice_number: str,
    client_name: str,
    client_address: str,
    client_nip: str,
    items: List[Dict],
    currency: str = "USD",
    notes: str = "",
) -> Optional[str]:
    """Create a Google Sheet invoice.

    Items format: [{"description": "...", "quantity": 1, "rate": 100.00}]
    Returns spreadsheet ID or None on failure.
    """
    subtotal = sum(item["quantity"] * item["rate"] for item in items)
    issue_date = datetime.now().strftime("%Y-%m-%d")

    result = google_api("POST", SHEETS_API, json_data={
        "properties": {"title": f"Invoice {invoice_number} — {client_name}"},
        "sheets": [{"properties": {"title": "Invoice", "index": 0}}],
    })

    spreadsheet_id = result.get("spreadsheetId")
    if not spreadsheet_id:
        logger.error("invoice_create_failed", error=result)
        return None

    rows = [
        ["INVOICE", "", "", invoice_number],
        [],
        ["From:", "", "To:", ""],
        [PYROX_COMPANY["name"], "", client_name, ""],
        [PYROX_COMPANY["address"], "", client_address, ""],
        [f"EIN: {PYROX_COMPANY['ein']}", "", f"NIP: {client_nip}" if client_nip else "", ""],
        [PYROX_COMPANY["email"], "", "", ""],
        [],
        ["Issue Date:", issue_date, "Due Date:", f"Net 30 from {issue_date}"],
        ["Currency:", currency, "", ""],
        [],
        ["#", "Description", "Qty", "Rate", "Amount"],
    ]

    for i, item in enumerate(items, 1):
        amount = item["quantity"] * item["rate"]
        rows.append([i, item["description"], item["quantity"], item["rate"], amount])

    rows.extend([
        [],
        ["", "", "", "Subtotal:", subtotal],
        ["", "", "", "Tax (0%):", 0],
        ["", "", "", "TOTAL:", subtotal],
        [],
        ["Payment Instructions:"],
        [f"Domestic Wire: {PYROX_COMPANY['bank_domestic']}"],
        [f"International: SWIFT {PYROX_COMPANY['bank_swift']}"],
        [f"Recipient: {PYROX_COMPANY['name']} (must match exactly)"],
        [],
        [f"Terms: {PYROX_COMPANY['terms']} — 1.5% monthly late fee"],
    ])

    if notes:
        rows.extend([[], ["Notes:", notes]])

    # Write data
    url = f"{SHEETS_API}/{spreadsheet_id}/values/Invoice!A1"
    google_api("PUT", url, json_data={"values": rows}, params={"valueInputOption": "USER_ENTERED"})

    logger.info("invoice_created", id=spreadsheet_id, invoice=invoice_number, total=subtotal)
    return spreadsheet_id


def list_invoices() -> List[Dict]:
    """List all invoice spreadsheets from Drive."""
    result = google_api("GET", f"{DRIVE_API}/files", params={
        "q": "name contains 'Invoice' and mimeType = 'application/vnd.google-apps.spreadsheet'",
        "fields": "files(id,name,modifiedTime)",
        "orderBy": "modifiedTime desc",
        "pageSize": 20,
    })
    files = result.get("files", [])
    return [{"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", "")} for f in files]


# ─── GOOGLE CALENDAR: Event management ──────────────────────────────────────

def create_calendar_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    attendees: Optional[List[str]] = None,
    timezone: str = "Europe/Warsaw",
) -> Optional[str]:
    """Create a Google Calendar event. Returns event ID or None."""
    event = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
    }
    if description:
        event["description"] = description
    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    result = google_api("POST", f"{CALENDAR_API}/calendars/primary/events", json_data=event)

    event_id = result.get("id")
    if not event_id:
        logger.error("event_create_failed", error=result)
        return None

    logger.info("event_created", id=event_id, summary=summary)
    return event_id


def list_upcoming_events(max_results: int = 10) -> List[Dict]:
    """List upcoming calendar events."""
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    result = google_api("GET", f"{CALENDAR_API}/calendars/primary/events", params={
        "timeMin": now_iso,
        "maxResults": max_results,
        "singleEvents": "true",
        "orderBy": "startTime",
    })

    events = result.get("items", [])
    return [
        {
            "id": e.get("id", ""),
            "summary": e.get("summary", ""),
            "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
            "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
            "attendees": [a.get("email", "") for a in e.get("attendees", [])],
        }
        for e in events
    ]


def delete_calendar_event(event_id: str) -> bool:
    """Delete a calendar event."""
    result = google_api("DELETE", f"{CALENDAR_API}/calendars/primary/events/{event_id}")
    return "error" not in result
