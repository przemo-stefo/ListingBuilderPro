# backend/api/admin_routes.py
# Purpose: Admin-only endpoints — overview, licenses, activity, system, costs
# NOT for: User-facing features or settings (those are in settings_routes.py)

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from api.dependencies import require_admin
from config import settings
from typing import Literal, Optional
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/me")
async def get_admin_status(request: Request):
    """Check if current user is an admin.

    WHY: Frontend calls this to show/hide admin UI sections.
    No auth guard — returns is_admin: false for non-admins instead of 403.
    """
    email = getattr(request.state, "user_email", "")
    is_admin = bool(email and email.lower() in settings.admin_emails_list)
    return {"is_admin": is_admin, "email": email}


@router.get("/overview")
async def get_admin_overview(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Dashboard overview — aggregated stats from all tables in one call.

    WHY: Mateusz needs a single glance at system health without clicking through tabs.
    """

    # --- Licenses by status ---
    lic_rows = db.execute(text(
        "SELECT status, COUNT(*) FROM premium_licenses GROUP BY status"
    )).fetchall()
    lic = {row[0]: row[1] for row in lic_rows}
    licenses = {
        "total": sum(lic.values()),
        "active": lic.get("active", 0),
        "expired": lic.get("expired", 0),
        "revoked": lic.get("revoked", 0),
    }

    # --- Products by status ---
    prod_rows = db.execute(text(
        "SELECT status, COUNT(*) FROM products GROUP BY status"
    )).fetchall()
    prod = {row[0]: row[1] for row in prod_rows}
    products = {
        "total": sum(prod.values()),
        "imported": prod.get("imported", 0),
        "optimized": prod.get("optimized", 0),
        "published": prod.get("published", 0),
        "failed": prod.get("failed", 0),
    }

    # --- Usage last 30 days (optimizer + research runs, unique IPs) ---
    usage = db.execute(text("""
        SELECT
            COUNT(*) AS total_runs,
            COUNT(*) FILTER (WHERE marketplace = 'research') AS research_runs,
            COUNT(DISTINCT client_ip) AS unique_ips
        FROM optimization_runs
        WHERE created_at >= NOW() - INTERVAL '30 days'
    """)).fetchone()
    usage_30d = {
        "optimizer_runs": usage[0] - usage[1],
        "research_runs": usage[1],
        "unique_ips": usage[2],
    }

    # --- OAuth connections ---
    oauth_rows = db.execute(text(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'active') FROM oauth_connections"
    )).fetchone()
    oauth_connections = {"total": oauth_rows[0], "active": oauth_rows[1]}

    # --- Alerts ---
    alert_row = db.execute(text("""
        SELECT
            COUNT(*),
            COUNT(*) FILTER (WHERE NOT acknowledged),
            COUNT(*) FILTER (WHERE severity = 'critical' AND NOT acknowledged)
        FROM alerts
    """)).fetchone()
    alerts = {
        "total": alert_row[0],
        "unacknowledged": alert_row[1],
        "critical": alert_row[2],
    }

    # --- MRR (Monthly Recurring Revenue) ---
    # WHY: active monthly subscriptions * 49 PLN = current MRR
    mrr_count = db.execute(text(
        "SELECT COUNT(*) FROM premium_licenses WHERE status = 'active' AND plan_type = 'monthly'"
    )).scalar() or 0

    return {
        "licenses": licenses,
        "products": products,
        "usage_30d": usage_30d,
        "oauth_connections": oauth_connections,
        "alerts": alerts,
        "mrr_pln": mrr_count * 49,
    }


@router.get("/licenses")
async def get_admin_licenses(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Paginated license list for admin management.

    WHY: Mateusz needs to see who has active licenses and when they expire.
    """

    total = db.execute(text("SELECT COUNT(*) FROM premium_licenses")).scalar()

    rows = db.execute(text("""
        SELECT id, email, status, plan_type, expires_at, created_at
        FROM premium_licenses
        ORDER BY created_at DESC, id
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset}).fetchall()

    return {
        "items": [
            {
                "id": str(row[0]),
                "email": row[1],
                "status": row[2],
                "plan_type": row[3],
                "expires_at": row[4].isoformat() if row[4] else None,
                "created_at": row[5].isoformat() if row[5] else None,
            }
            for row in rows
        ],
        "total": total,
    }


class LicenseUpdateRequest(BaseModel):
    """WHY: Typed request — validates action + days at Pydantic level."""
    action: Literal["revoke", "extend"]
    days: Optional[int] = Field(default=30, ge=1, le=365)


@router.patch("/licenses/{license_id}")
async def update_license(
    license_id: str,
    body: LicenseUpdateRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Admin action: revoke or extend a license.

    WHY: Mateusz needs to manage licenses without touching the DB directly.
    """
    # WHY: Verify license exists before modifying
    existing = db.execute(text(
        "SELECT id, email, status, plan_type, expires_at FROM premium_licenses WHERE id = CAST(:id AS uuid)"
    ), {"id": license_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="License not found")

    if body.action == "revoke":
        db.execute(text(
            "UPDATE premium_licenses SET status = 'revoked', updated_at = NOW() WHERE id = CAST(:id AS uuid)"
        ), {"id": license_id})
        db.commit()
        logger.info("license_revoked", license_id=license_id, email=existing[1])

    elif body.action == "extend":
        # WHY: If expires_at is NULL or in the past, extend from NOW; otherwise extend from current expiry
        db.execute(text("""
            UPDATE premium_licenses
            SET expires_at = COALESCE(
                GREATEST(expires_at, NOW()),
                NOW()
            ) + MAKE_INTERVAL(days => :days),
            status = 'active',
            updated_at = NOW()
            WHERE id = CAST(:id AS uuid)
        """), {"id": license_id, "days": body.days})
        db.commit()
        logger.info("license_extended", license_id=license_id, email=existing[1], days=body.days)

    # Return updated license
    updated = db.execute(text(
        "SELECT id, email, status, plan_type, expires_at, created_at FROM premium_licenses WHERE id = CAST(:id AS uuid)"
    ), {"id": license_id}).fetchone()

    return {
        "id": str(updated[0]),
        "email": updated[1],
        "status": updated[2],
        "plan_type": updated[3],
        "expires_at": updated[4].isoformat() if updated[4] else None,
        "created_at": updated[5].isoformat() if updated[5] else None,
    }


