# backend/api/admin_routes.py
# Purpose: Admin-only endpoints — overview, licenses, cost dashboard for Mateusz
# NOT for: User-facing features or settings (those are in settings_routes.py)

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from api.dependencies import require_admin
from config import settings

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


@router.get("/costs")
async def get_cost_dashboard(
    days: int = Query(default=30, ge=1, le=365),  # WHY: Validate range server-side
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),  # WHY: Only admins can see cost data
):
    """Cost dashboard — total spend, per-provider breakdown, daily trend.

    WHY: Mateusz needs to see how much API usage costs so he can control expenses.
    Data comes from optimization_runs.trace_data (already tracked per run).
    """

    # --- Totals ---
    totals = db.execute(text("""
        SELECT
            COUNT(*) AS total_runs,
            COALESCE(SUM((trace_data->>'total_tokens')::numeric), 0) AS total_tokens,
            COALESCE(SUM((trace_data->>'total_prompt_tokens')::numeric), 0) AS prompt_tokens,
            COALESCE(SUM((trace_data->>'total_completion_tokens')::numeric), 0) AS completion_tokens,
            COALESCE(SUM((trace_data->>'estimated_cost_usd')::numeric), 0) AS total_cost_usd,
            COALESCE(AVG((trace_data->>'estimated_cost_usd')::numeric), 0) AS avg_cost_per_run
        FROM optimization_runs
        WHERE trace_data IS NOT NULL
          AND created_at >= NOW() - MAKE_INTERVAL(days => :days)
    """), {"days": days}).fetchone()

    # --- Per-provider breakdown ---
    # WHY: Model name is in spans[0].model — extract with JSONB operators
    by_provider = db.execute(text("""
        SELECT
            COALESCE(trace_data->'spans'->0->>'model', 'unknown') AS model,
            COUNT(*) AS runs,
            COALESCE(SUM((trace_data->>'total_tokens')::numeric), 0) AS tokens,
            COALESCE(SUM((trace_data->>'estimated_cost_usd')::numeric), 0) AS cost_usd
        FROM optimization_runs
        WHERE trace_data IS NOT NULL
          AND created_at >= NOW() - MAKE_INTERVAL(days => :days)
        GROUP BY model
        ORDER BY cost_usd DESC
    """), {"days": days}).fetchall()

    # --- Daily trend (last N days) ---
    daily = db.execute(text("""
        SELECT
            DATE(created_at) AS day,
            COUNT(*) AS runs,
            COALESCE(SUM((trace_data->>'total_tokens')::numeric), 0) AS tokens,
            COALESCE(SUM((trace_data->>'estimated_cost_usd')::numeric), 0) AS cost_usd
        FROM optimization_runs
        WHERE trace_data IS NOT NULL
          AND created_at >= NOW() - MAKE_INTERVAL(days => :days)
        GROUP BY DATE(created_at)
        ORDER BY day DESC
    """), {"days": days}).fetchall()

    return {
        "period_days": days,
        "totals": {
            "runs": totals[0],
            "total_tokens": int(totals[1]),
            "prompt_tokens": int(totals[2]),
            "completion_tokens": int(totals[3]),
            "total_cost_usd": round(float(totals[4]), 4),
            "avg_cost_per_run_usd": round(float(totals[5]), 6),
        },
        "by_provider": [
            {
                "model": row[0],
                "runs": row[1],
                "tokens": int(row[2]),
                "cost_usd": round(float(row[3]), 4),
            }
            for row in by_provider
        ],
        "daily": [
            {
                "date": row[0].isoformat(),
                "runs": row[1],
                "tokens": int(row[2]),
                "cost_usd": round(float(row[3]), 4),
            }
            for row in daily
        ],
    }


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

    return {
        "licenses": licenses,
        "products": products,
        "usage_30d": usage_30d,
        "oauth_connections": oauth_connections,
        "alerts": alerts,
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
        SELECT email, status, plan_type, expires_at, created_at
        FROM premium_licenses
        ORDER BY created_at DESC, id
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset}).fetchall()

    return {
        "items": [
            {
                "email": row[0],
                "status": row[1],
                "plan_type": row[2],
                "expires_at": row[3].isoformat() if row[3] else None,
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ],
        "total": total,
    }
