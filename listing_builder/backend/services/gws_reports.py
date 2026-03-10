# backend/services/gws_reports.py
# Purpose: Generate Google Sheets/Gmail reports from LBP data via gws CLI
# NOT for: Analytics queries (analytics_routes.py) or PDF export (separate)

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()


def _gws(args: List[str], input_json: Optional[dict] = None) -> dict:
    """Run a gws CLI command and return parsed JSON output.

    WHY: Subprocess instead of SDK — gws handles auth, token refresh, retries.
    """
    cmd = ["gws"] + args
    kwargs: dict = {"capture_output": True, "text": True, "timeout": 30}
    try:
        result = subprocess.run(cmd, **kwargs)
        if result.returncode != 0:
            logger.warning("gws_cmd_failed", args=args[:3], stderr=result.stderr[:200])
            return {"error": result.stderr[:500]}
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except subprocess.TimeoutExpired:
        logger.error("gws_cmd_timeout", args=args[:3])
        return {"error": "gws command timed out"}
    except json.JSONDecodeError:
        return {"raw": result.stdout[:500]}


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
    # Step 1: Create spreadsheet
    create_result = _gws([
        "sheets", "spreadsheets", "create",
        "--json", json.dumps({
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": "Podsumowanie", "index": 0}},
                {"properties": {"title": "Optymalizacje", "index": 1}},
                {"properties": {"title": "Przychody", "index": 2}},
                {"properties": {"title": "Magazyn", "index": 3}},
            ],
        }),
    ])

    spreadsheet_id = create_result.get("spreadsheetId")
    if not spreadsheet_id:
        logger.error("gws_sheet_create_failed", error=create_result)
        return None

    logger.info("gws_sheet_created", id=spreadsheet_id, title=title)

    # Step 2: Fill "Podsumowanie" tab
    summary_rows = _build_summary_rows(optimization_data, analytics_data, inventory_data)
    _write_sheet_values(spreadsheet_id, "Podsumowanie!A1", summary_rows)

    # Step 3: Fill "Optymalizacje" tab
    opt_rows = _build_optimization_rows(optimization_data)
    _write_sheet_values(spreadsheet_id, "Optymalizacje!A1", opt_rows)

    # Step 4: Fill "Przychody" tab
    rev_rows = _build_revenue_rows(analytics_data)
    _write_sheet_values(spreadsheet_id, "Przychody!A1", rev_rows)

    # Step 5: Fill "Magazyn" tab
    inv_rows = _build_inventory_rows(inventory_data)
    _write_sheet_values(spreadsheet_id, "Magazyn!A1", inv_rows)

    return spreadsheet_id


def _write_sheet_values(spreadsheet_id: str, range_str: str, values: List[List]) -> None:
    """Write rows to a Google Sheet range."""
    _gws([
        "sheets", "spreadsheets", "values", "update",
        "--params", json.dumps({
            "spreadsheetId": spreadsheet_id,
            "range": range_str,
            "valueInputOption": "USER_ENTERED",
        }),
        "--json", json.dumps({"values": values}),
    ])


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
        ["📊 Raport LBP — OctoHelper", "", now],
        [],
        ["OPTYMALIZACJE"],
        ["Łączna liczba", total_opts],
        ["Średnie pokrycie słów kluczowych", f"{avg_coverage}%"],
        ["Zgodne z regulaminem", f"{compliant}/{total_opts}"],
        [],
        ["PRZYCHODY"],
        ["Łączny przychód", total_rev],
        ["Zamówienia", total_orders],
        ["Średnia wartość zamówienia", avg_order],
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
            o.get("created_at", "")[:16],
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
    rows.append(["Marketplace", "Przychód", "Zamówienia", "Udział %"])
    for mp in analytics.get("revenue_by_marketplace", []):
        rows.append([
            mp.get("marketplace", ""),
            mp.get("revenue", 0),
            mp.get("orders", 0),
            f"{mp.get('percentage', 0)}%",
        ])

    rows.append([])
    rows.append(["TREND MIESIĘCZNY"])
    rows.append(["Miesiąc", "Przychód", "Zamówienia"])
    for m in analytics.get("monthly_revenue", []):
        rows.append([m.get("month", ""), m.get("revenue", 0), m.get("orders", 0)])

    rows.append([])
    rows.append(["TOP PRODUKTY"])
    rows.append(["Produkt", "Marketplace", "Przychód", "Sprzedane szt.", "CR %"])
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
    header = ["SKU", "Produkt", "Marketplace", "Ilość", "Punkt zamówienia",
              "Dni zapasu", "Koszt jedn.", "Wartość", "Status"]
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


def send_report_email(
    to_email: str,
    subject: str,
    spreadsheet_id: str,
    summary_text: str,
) -> bool:
    """Send report notification via Gmail with link to the spreadsheet.

    WHY: gws +send handles OAuth, threading, encoding. No SMTP setup needed.
    """
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    body = (
        f"{summary_text}\n\n"
        f"📊 Pełny raport: {sheet_url}\n\n"
        f"---\n"
        f"Wygenerowano automatycznie przez OctoHelper\n"
        f"https://panel.octohelper.com"
    )

    result = _gws([
        "gmail", "+send",
        "--to", to_email,
        "--subject", subject,
        "--body", body,
    ])

    if "error" in result:
        logger.error("gws_email_failed", to=to_email, error=result["error"][:200])
        return False

    logger.info("gws_email_sent", to=to_email, subject=subject)
    return True


def share_spreadsheet(spreadsheet_id: str, email: str, role: str = "reader") -> bool:
    """Share spreadsheet with a specific email."""
    result = _gws([
        "drive", "permissions", "create",
        "--params", json.dumps({"fileId": spreadsheet_id}),
        "--json", json.dumps({
            "type": "user",
            "role": role,
            "emailAddress": email,
        }),
    ])
    return "error" not in result
