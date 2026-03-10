# backend/services/gws_office.py
# Purpose: PYROX AI office automation via gws CLI — Docs templates, Sheets invoices, Calendar events
# NOT for: LBP reports (gws_reports.py) or analytics (analytics_routes.py)

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

import structlog

from services.gws_reports import _gws

logger = structlog.get_logger()


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
    # WHY: Markdown-style header in Doc so team knows this is a template
    content = (
        f"SZABLON EMAIL: {template_name}\n"
        f"Temat: {subject}\n"
        f"Zmienne: {', '.join(variables)}\n"
        f"---\n\n"
        f"{html_body}"
    )

    result = _gws([
        "docs", "documents", "create",
        "--json", json.dumps({
            "title": f"[Drip] {template_name}",
            "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": content}}]}}]},
        }),
    ])

    doc_id = result.get("documentId")
    if not doc_id:
        logger.error("gws_doc_create_failed", template=template_name, error=result)
        return None

    logger.info("gws_doc_created", id=doc_id, template=template_name)
    return doc_id


def read_drip_template(doc_id: str) -> Optional[str]:
    """Read a Google Doc template content.

    WHY: n8n Code node can fetch template from Docs before sending email,
    instead of hardcoding HTML in workflow JSON.
    """
    result = _gws(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id})])

    if "error" in result:
        return None

    # WHY: Extract text from Doc body — Docs API returns nested structure
    body = result.get("body", {})
    content = body.get("content", [])
    text_parts = []
    for element in content:
        for para_elem in element.get("paragraph", {}).get("elements", []):
            text_run = para_elem.get("textRun", {})
            if "content" in text_run:
                text_parts.append(text_run["content"])

    full_text = "".join(text_parts)
    # WHY: Skip header (everything before "---\n\n") — return only email body
    if "---\n\n" in full_text:
        return full_text.split("---\n\n", 1)[1]
    return full_text


def list_drip_templates() -> List[Dict]:
    """List all drip campaign templates from Drive.

    WHY: Search by "[Drip]" prefix — all templates are named "[Drip] Template Name".
    """
    result = _gws([
        "drive", "files", "list",
        "--params", json.dumps({
            "q": "name contains '[Drip]' and mimeType = 'application/vnd.google-apps.document'",
            "fields": "files(id,name,modifiedTime)",
            "orderBy": "modifiedTime desc",
        }),
    ])

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

    WHY: Google Sheets = shareable, printable, auto-updates. Replaces Zoho for simple invoices.
    Items format: [{"description": "...", "quantity": 1, "rate": 100.00}]

    Returns spreadsheet ID or None on failure.
    """
    now = datetime.now()
    issue_date = now.strftime("%Y-%m-%d")
    due_date_str = now.strftime("%Y-%m-%d")  # Net 30 calculated in sheet

    # Build item rows
    subtotal = sum(item["quantity"] * item["rate"] for item in items)

    create_result = _gws([
        "sheets", "spreadsheets", "create",
        "--json", json.dumps({
            "properties": {"title": f"Invoice {invoice_number} — {client_name}"},
            "sheets": [{"properties": {"title": "Invoice", "index": 0}}],
        }),
    ])

    spreadsheet_id = create_result.get("spreadsheetId")
    if not spreadsheet_id:
        logger.error("gws_invoice_create_failed", error=create_result)
        return None

    # WHY: Build invoice layout — header, client info, line items, totals, payment info
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

    from services.gws_reports import _write_sheet_values
    _write_sheet_values(spreadsheet_id, "Invoice!A1", rows)

    logger.info("gws_invoice_created", id=spreadsheet_id, invoice=invoice_number, total=subtotal)
    return spreadsheet_id


def list_invoices() -> List[Dict]:
    """List all invoice spreadsheets from Drive."""
    result = _gws([
        "drive", "files", "list",
        "--params", json.dumps({
            "q": "name contains 'Invoice' and mimeType = 'application/vnd.google-apps.spreadsheet'",
            "fields": "files(id,name,modifiedTime)",
            "orderBy": "modifiedTime desc",
            "pageSize": 20,
        }),
    ])
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
    """Create a Google Calendar event.

    WHY: gws CLI handles OAuth + timezone conversion. Attendees get invite emails automatically.

    Returns event ID or None on failure.
    """
    event = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
    }
    if description:
        event["description"] = description
    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    result = _gws([
        "calendar", "events", "insert",
        "--params", json.dumps({"calendarId": "primary"}),
        "--json", json.dumps(event),
    ])

    event_id = result.get("id")
    if not event_id:
        logger.error("gws_event_create_failed", error=result)
        return None

    logger.info("gws_event_created", id=event_id, summary=summary)
    return event_id


def list_upcoming_events(max_results: int = 10) -> List[Dict]:
    """List upcoming calendar events."""
    now_iso = datetime.now().isoformat() + "Z"
    result = _gws([
        "calendar", "events", "list",
        "--params", json.dumps({
            "calendarId": "primary",
            "timeMin": now_iso,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }),
    ])

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
    result = _gws([
        "calendar", "events", "delete",
        "--params", json.dumps({"calendarId": "primary", "eventId": event_id}),
    ])
    return "error" not in result
