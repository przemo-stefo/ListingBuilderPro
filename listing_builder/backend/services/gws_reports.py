# backend/services/gws_reports.py
# Purpose: Generate Google Sheets/Gmail reports from LBP data via REST API
# NOT for: Analytics queries (analytics_routes.py) or PDF export (separate)

from __future__ import annotations

import base64
from datetime import datetime
from typing import Dict, List, Optional

import structlog

from services.gws_auth import google_api

logger = structlog.get_logger()

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
DRIVE_API = "https://www.googleapis.com/drive/v3"


def create_report_spreadsheet(
    title: str,
    optimization_data: List[dict],
    analytics_data: dict,
    inventory_data: List[dict],
) -> Optional[str]:
    """Create a Google Sheet with LBP report data.

    Returns spreadsheet ID or None on failure.
    WHY: Google Sheets = shareable, auto-updates, Mateusz can view on phone.
    """
    result = google_api("POST", SHEETS_API, json_data={
        "properties": {"title": title},
        "sheets": [
            {"properties": {"title": "Podsumowanie", "index": 0}},
            {"properties": {"title": "Optymalizacje", "index": 1}},
            {"properties": {"title": "Przychody", "index": 2}},
            {"properties": {"title": "Magazyn", "index": 3}},
        ],
    })

    spreadsheet_id = result.get("spreadsheetId")
    if not spreadsheet_id:
        logger.error("sheet_create_failed", error=result)
        return None

    logger.info("sheet_created", id=spreadsheet_id, title=title)

    summary_rows = _build_summary_rows(optimization_data, analytics_data, inventory_data)
    _write_values(spreadsheet_id, "Podsumowanie!A1", summary_rows)

    opt_rows = _build_optimization_rows(optimization_data)
    _write_values(spreadsheet_id, "Optymalizacje!A1", opt_rows)

    rev_rows = _build_revenue_rows(analytics_data)
    _write_values(spreadsheet_id, "Przychody!A1", rev_rows)

    inv_rows = _build_inventory_rows(inventory_data)
    _write_values(spreadsheet_id, "Magazyn!A1", inv_rows)

    return spreadsheet_id


def _write_values(spreadsheet_id: str, range_str: str, values: List[List]) -> None:
    """Write rows to a Google Sheet range via REST API."""
    url = f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}"
    google_api("PUT", url, json_data={"values": values}, params={"valueInputOption": "USER_ENTERED"})


def send_report_email(
    to_email: str,
    subject: str,
    spreadsheet_id: str,
    summary_text: str,
) -> bool:
    """Send report notification via Gmail with link to the spreadsheet."""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    body_text = (
        f"{summary_text}\n\n"
        f"Pelny raport: {sheet_url}\n\n"
        f"---\n"
        f"Wygenerowano automatycznie przez OctoHelper\n"
        f"https://panel.octohelper.com"
    )

    # WHY: Gmail API requires base64url-encoded RFC 2822 message
    message = f"To: {to_email}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body_text}"
    raw = base64.urlsafe_b64encode(message.encode()).decode()

    result = google_api("POST", f"{GMAIL_API}/messages/send", json_data={"raw": raw})

    if "error" in result:
        logger.error("email_send_failed", to=to_email, error=str(result["error"])[:200])
        return False

    logger.info("email_sent", to=to_email, subject=subject)
    return True


def share_spreadsheet(spreadsheet_id: str, email: str, role: str = "reader") -> bool:
    """Share spreadsheet with a specific email."""
    result = google_api("POST", f"{DRIVE_API}/files/{spreadsheet_id}/permissions", json_data={
        "type": "user",
        "role": role,
        "emailAddress": email,
    })
    return "error" not in result


def _build_summary_rows(
    opt_data: List[dict], analytics: dict, inventory: List[dict],
) -> List[List]:
    """Summary tab: KPIs at a glance."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_opts = len(opt_data)
    avg_coverage = (
        round(sum(o.get("coverage_pct", 0) or 0 for o in opt_data) / total_opts, 1)
        if total_opts > 0 else 0
    )
    compliant = sum(1 for o in opt_data if o.get("compliance_status") == "ok")

    total_rev = analytics.get("total_revenue", 0)
    total_orders = analytics.get("total_orders", 0)
    avg_order = analytics.get("avg_order_value", 0)

    in_stock = sum(1 for i in inventory if i.get("status") == "in_stock")
    low_stock = sum(1 for i in inventory if i.get("status") == "low_stock")
    oos = sum(1 for i in inventory if i.get("status") == "out_of_stock")

    return [
        ["Raport LBP — OctoHelper", "", now],
        [],
        ["OPTYMALIZACJE"],
        ["Laczna liczba", total_opts],
        ["Srednie pokrycie slow kluczowych", f"{avg_coverage}%"],
        ["Zgodne z regulaminem", f"{compliant}/{total_opts}"],
        [],
        ["PRZYCHODY"],
        ["Laczny przychod", total_rev],
        ["Zamowienia", total_orders],
        ["Srednia wartosc zamowienia", avg_order],
        [],
        ["MAGAZYN"],
        ["W magazynie", in_stock],
        ["Niski stan", low_stock],
        ["Brak w magazynie", oos],
    ]


def _build_optimization_rows(opt_data: List[dict]) -> List[List]:
    """Optimization history tab."""
    header = ["Data", "Produkt", "Marka", "Marketplace", "Tryb", "Pokrycie %", "Compliance"]
    rows = [header]
    for o in opt_data[:100]:
        rows.append([
            str(o.get("created_at", ""))[:16],
            (o.get("product_title") or "")[:60],
            (o.get("brand") or "")[:30],
            o.get("marketplace", ""),
            o.get("mode", ""),
            o.get("coverage_pct", ""),
            o.get("compliance_status", ""),
        ])
    return rows


def _build_revenue_rows(analytics: dict) -> List[List]:
    """Revenue breakdown tab."""
    rows = [["PRZYCHODY WG MARKETPLACE"]]
    rows.append(["Marketplace", "Przychod", "Zamowienia", "Udzial %"])
    for mp in analytics.get("revenue_by_marketplace", []):
        rows.append([
            mp.get("marketplace", ""),
            mp.get("revenue", 0),
            mp.get("orders", 0),
            f"{mp.get('percentage', 0)}%",
        ])

    rows.append([])
    rows.append(["TREND MIESIECZNY"])
    rows.append(["Miesiac", "Przychod", "Zamowienia"])
    for m in analytics.get("monthly_revenue", []):
        rows.append([m.get("month", ""), m.get("revenue", 0), m.get("orders", 0)])

    rows.append([])
    rows.append(["TOP PRODUKTY"])
    rows.append(["Produkt", "Marketplace", "Przychod", "Sprzedane szt.", "CR %"])
    for p in analytics.get("top_products", []):
        rows.append([
            (p.get("title") or "")[:60],
            p.get("marketplace", ""),
            p.get("revenue", 0),
            p.get("units_sold", 0),
            p.get("conversion_rate", 0),
        ])
    return rows


def _build_inventory_rows(inventory: List[dict]) -> List[List]:
    """Inventory status tab."""
    header = ["SKU", "Produkt", "Marketplace", "Ilosc", "Punkt zamowienia",
              "Dni zapasu", "Koszt jedn.", "Wartosc", "Status"]
    rows = [header]
    for i in inventory[:50]:
        rows.append([
            i.get("sku", ""),
            (i.get("product_title") or "")[:50],
            i.get("marketplace", ""),
            i.get("quantity", 0),
            i.get("reorder_point", 0),
            i.get("days_of_supply", 0),
            i.get("unit_cost", 0),
            i.get("total_value", 0),
            i.get("status", ""),
        ])
    return rows
