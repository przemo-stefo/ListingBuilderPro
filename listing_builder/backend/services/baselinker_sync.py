# backend/services/baselinker_sync.py
# Purpose: Sync BOL.com open orders → BaseLinker via cron (every 15 min)
# NOT for: BOL.com offer fetching (that's bol_api.py) or BaseLinker product sync

import json
import httpx
import structlog
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from config import settings
from models.baselinker_sync import BaseLinkerSyncLog
from models.oauth_connection import OAuthConnection
from services.bol_api import validate_bol_credentials

logger = structlog.get_logger()

BOL_API_BASE = "https://api.bol.com/retailer"
BOL_ACCEPT = "application/vnd.retailer.v10+json"
BASELINKER_URL = "https://api.baselinker.com/connector.php"

# WHY: PII fields in BOL orders — strip before storing in DB (recursive, all levels)
_PII_KEYS = {
    "firstName", "surname", "email", "streetName", "houseNumber",
    "houseNumberExtension", "zipCode", "phone", "company",
    "vatNumber", "chamberOfCommerceNumber", "deliveryPhoneNumber",
}


def _strip_pii(data):
    """Recursively remove customer PII from BOL order before storing in sync log.

    WHY: GDPR — we only need orderId, items, and status for debugging.
    Recursive to catch PII in nested structures regardless of BOL API schema changes.
    """
    if isinstance(data, dict):
        return {k: "***" if k in _PII_KEYS else _strip_pii(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_strip_pii(item) for item in data]
    return data


async def sync_bol_orders(session_factory) -> Dict:
    """Main cron entry point — fetch BOL open orders, push new ones to BaseLinker.

    WHY session_factory: APScheduler passes it as arg, same pattern as poll_marketplace.
    """
    db: Session = session_factory()
    try:
        token = await _get_bol_token(db)
        if not token:
            logger.warning("baselinker_sync_skip", reason="no BOL token")
            return {"synced": 0, "skipped": 0, "errors": 0}

        orders = await _fetch_bol_open_orders(token)
        if not orders:
            return {"synced": 0, "skipped": 0, "errors": 0}

        # WHY: Batch dedup — one query instead of N queries per order
        all_bol_ids = [o.get("orderId", "") for o in orders if o.get("orderId")]
        existing_ids = set()
        if all_bol_ids:
            rows = db.query(BaseLinkerSyncLog.bol_order_id).filter(
                BaseLinkerSyncLog.bol_order_id.in_(all_bol_ids)
            ).all()
            existing_ids = {r[0] for r in rows}

        synced = 0
        skipped = 0
        errors = 0

        for order in orders:
            bol_order_id = order.get("orderId", "")
            if not bol_order_id:
                continue

            if bol_order_id in existing_ids:
                skipped += 1
                continue

            result = await _push_to_baselinker(order, settings.baselinker_api_token)

            log_entry = BaseLinkerSyncLog(
                bol_order_id=bol_order_id,
                baselinker_order_id=result.get("order_id"),
                status="synced" if result["ok"] else "error",
                error_message=result.get("error"),
                bol_order_data=_strip_pii(order),
            )
            db.add(log_entry)
            db.commit()

            if result["ok"]:
                synced += 1
            else:
                errors += 1

        logger.info("baselinker_sync_done", synced=synced, skipped=skipped, errors=errors)
        return {"synced": synced, "skipped": skipped, "errors": errors}

    except Exception as e:
        logger.error("baselinker_sync_failed", error=str(e))
        return {"synced": 0, "skipped": 0, "errors": 1, "fatal": str(e)}
    finally:
        db.close()


async def _get_bol_token(db: Session) -> Optional[str]:
    """Get a valid BOL.com token from any active connection.

    WHY reuse OAuthConnection: BOL credentials are already stored there
    from the Integracje connect flow — no need to duplicate in config.
    """
    conn = db.query(OAuthConnection).filter(
        OAuthConnection.marketplace == "bol",
        OAuthConnection.status == "active",
    ).first()

    if not conn:
        return None

    # WHY: Reuse _get_fresh_token pattern from bol_api.py
    now = datetime.now(timezone.utc)
    if (conn.access_token
            and conn.token_expires_at
            and conn.token_expires_at > now + timedelta(seconds=60)):
        return conn.access_token

    client_id = conn.raw_data.get("client_id", "") if conn.raw_data else ""
    client_secret = conn.raw_data.get("client_secret", "") if conn.raw_data else ""

    if not client_id or not client_secret:
        return None

    result = await validate_bol_credentials(client_id, client_secret)
    if not result["valid"]:
        conn.status = "expired"
        conn.updated_at = now
        db.commit()
        return None

    conn.access_token = result["token"]
    conn.token_expires_at = now + timedelta(seconds=result["expires_in"])
    conn.updated_at = now
    db.commit()
    return conn.access_token


async def _fetch_bol_open_orders(token: str) -> List[Dict]:
    """Fetch all open FBR orders from BOL.com (paginated).

    WHY paginated: BOL returns max 50 orders/page, same as fetch_bol_offers().
    """
    all_orders: List[Dict] = []
    page = 1
    max_pages = 20  # WHY: Guard against infinite loop — 20 * 50 = 1K orders max

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(max_pages):
                resp = await client.get(
                    f"{BOL_API_BASE}/orders",
                    params={"status": "OPEN", "fulfilment-method": "FBR", "page": page},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": BOL_ACCEPT,
                    },
                )

                if resp.status_code != 200:
                    logger.warning("bol_orders_fetch_failed", status=resp.status_code, page=page)
                    break

                data = resp.json()
                orders = data.get("orders", [])
                all_orders.extend(orders)

                # WHY: Fewer than 50 = last page
                if len(orders) < 50:
                    break
                page += 1

        logger.info("bol_orders_fetched", count=len(all_orders))
        return all_orders

    except Exception as e:
        logger.error("bol_orders_error", error=str(e))
        return all_orders  # WHY: Return what we got so far


async def _push_to_baselinker(bol_order: Dict, api_token: str) -> Dict:
    """Send one BOL order to BaseLinker via addOrder."""
    try:
        mapped = _map_bol_to_baselinker(bol_order)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                BASELINKER_URL,
                data={
                    "token": api_token,
                    "method": "addOrder",
                    "parameters": _json_str(mapped),
                },
            )

        result = resp.json()

        if result.get("status") == "SUCCESS":
            order_id = str(result.get("order_id", ""))
            logger.info("baselinker_order_created", bol_id=bol_order.get("orderId"), bl_id=order_id)
            return {"ok": True, "order_id": order_id}

        error_msg = result.get("error_message", "Unknown BaseLinker error")
        logger.warning("baselinker_order_failed", bol_id=bol_order.get("orderId"), error=error_msg)
        return {"ok": False, "error": error_msg}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def _map_bol_to_baselinker(bol_order: Dict) -> Dict:
    """Map BOL.com order structure → BaseLinker addOrder params."""
    shipment = bol_order.get("shipmentDetails", {})
    billing = bol_order.get("billingDetails", {})
    items = bol_order.get("orderItems", [])

    # WHY: BaseLinker expects unix timestamp for date_add
    placed = bol_order.get("orderPlacedDateTime", "")
    date_add = int(datetime.now(timezone.utc).timestamp())
    if placed:
        try:
            dt = datetime.fromisoformat(placed.replace("Z", "+00:00"))
            date_add = int(dt.timestamp())
        except (ValueError, TypeError):
            pass  # WHY: Keep fallback to now() set above

    products = []
    for item in items:
        products.append({
            "name": item.get("title", ""),
            "sku": item.get("ean", ""),
            "price_brutto": float(item.get("unitPrice", 0)),
            "quantity": int(item.get("quantity", 1)),
        })

    return {
        "order_source": "bol.com",
        "date_add": date_add,
        "currency": "EUR",
        "delivery_fullname": f"{shipment.get('firstName', '')} {shipment.get('surname', '')}".strip(),
        "delivery_address": f"{shipment.get('streetName', '')} {shipment.get('houseNumber', '')}".strip(),
        "delivery_city": shipment.get("city", ""),
        "delivery_postcode": shipment.get("zipCode", ""),
        "delivery_country_code": shipment.get("countryCode", "NL"),
        "email": shipment.get("email", ""),
        "invoice_fullname": f"{billing.get('firstName', '')} {billing.get('surname', '')}".strip(),
        "invoice_address": f"{billing.get('streetName', '')} {billing.get('houseNumber', '')}".strip(),
        "invoice_city": billing.get("city", ""),
        "invoice_postcode": billing.get("zipCode", ""),
        "invoice_country_code": billing.get("countryCode", "NL"),
        "products": products,
        "custom_extra_fields": {
            "bol_order_id": bol_order.get("orderId", ""),
        },
    }


def _json_str(data: Dict) -> str:
    """Serialize to JSON string for BaseLinker form data."""
    return json.dumps(data)
