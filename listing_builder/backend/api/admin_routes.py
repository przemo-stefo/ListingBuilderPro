# backend/api/admin_routes.py
# Purpose: Admin-only endpoints — overview, licenses, activity, system, costs
# NOT for: User-facing features or settings (those are in settings_routes.py)

from fastapi import APIRouter, Depends, Query, Request, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine
from api.dependencies import require_admin
from config import settings
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


@router.patch("/licenses/{license_id}")
async def update_license(
    license_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Admin action: revoke or extend a license.

    WHY: Mateusz needs to manage licenses without touching the DB directly.
    """
    action = body.get("action")
    if action not in ("revoke", "extend"):
        raise HTTPException(status_code=400, detail="action must be 'revoke' or 'extend'")

    # WHY: Verify license exists before modifying
    existing = db.execute(text(
        "SELECT id, email, status, plan_type, expires_at FROM premium_licenses WHERE id = CAST(:id AS uuid)"
    ), {"id": license_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="License not found")

    if action == "revoke":
        db.execute(text(
            "UPDATE premium_licenses SET status = 'revoked', updated_at = NOW() WHERE id = CAST(:id AS uuid)"
        ), {"id": license_id})
        db.commit()
        logger.info("license_revoked", license_id=license_id, email=existing[1])

    elif action == "extend":
        days = body.get("days", 30)
        if not isinstance(days, int) or days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="days must be 1-365")
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
        """), {"id": license_id, "days": days})
        db.commit()
        logger.info("license_extended", license_id=license_id, email=existing[1], days=days)

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


@router.get("/oauth-connections")
async def get_oauth_connections(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """OAuth connections grouped by user — which marketplaces each user connected.

    WHY: Admin needs to see who connected what without checking each marketplace.
    """
    rows = db.execute(text("""
        SELECT user_id, marketplace, status, seller_name, created_at
        FROM oauth_connections
        ORDER BY created_at DESC
    """)).fetchall()

    return {
        "items": [
            {
                "user_id": row[0],
                "marketplace": row[1],
                "status": row[2],
                "seller_name": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ],
    }


@router.get("/activity")
async def get_activity_log(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Recent activity — optimizations, imports, compliance reports.

    WHY: Mateusz needs to see what's happening in the system without checking each feature.
    """

    optimizations = db.execute(text("""
        SELECT id, product_title, marketplace, mode, client_ip, created_at
        FROM optimization_runs
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => :days)
        ORDER BY created_at DESC
        LIMIT 50
    """), {"days": days}).fetchall()

    imports = db.execute(text("""
        SELECT id, source, status, total_products, created_at
        FROM import_jobs
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => :days)
        ORDER BY created_at DESC
        LIMIT 20
    """), {"days": days}).fetchall()

    reports = db.execute(text("""
        SELECT id, marketplace, total_products, overall_score, created_at
        FROM compliance_reports
        WHERE created_at >= NOW() - MAKE_INTERVAL(days => :days)
        ORDER BY created_at DESC
        LIMIT 20
    """), {"days": days}).fetchall()

    return {
        "period_days": days,
        "optimizations": [
            {
                "id": row[0],
                "title": row[1],
                "marketplace": row[2],
                "mode": row[3],
                "client_ip": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            }
            for row in optimizations
        ],
        "imports": [
            {
                "id": row[0],
                "source": row[1],
                "status": str(row[2]),
                "total_products": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in imports
        ],
        "compliance_reports": [
            {
                "id": row[0],
                "marketplace": row[1],
                "total_products": row[2],
                "overall_score": round(float(row[3]), 1) if row[3] else 0,
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in reports
        ],
    }


@router.get("/system")
async def get_system_status(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """System health — DB, Groq keys, config.

    WHY: Quick system status check without SSH-ing into the server.
    """

    # --- Database status ---
    try:
        pool = engine.pool
        db_status = {
            "status": "connected",
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
        }
    except Exception as e:
        db_status = {"status": "error", "error": str(e)}

    # --- Groq keys health ---
    # WHY: Check each key with a lightweight models.list() call
    groq_keys = []
    for i, key in enumerate(settings.groq_api_keys):
        try:
            from groq import Groq
            client = Groq(api_key=key, timeout=5.0)
            client.models.list()
            groq_keys.append({"index": i + 1, "status": "ok", "error": None})
        except Exception as e:
            groq_keys.append({"index": i + 1, "status": "error", "error": str(e)[:100]})

    # --- Config summary (safe to expose to admin) ---
    config_info = {
        "groq_model": settings.groq_model,
        "admin_emails": settings.admin_emails_list,
        "cors_origins_count": len(settings.cors_origins_list),
        "is_production": settings.is_production,
        "rag_mode": settings.rag_mode,
    }

    return {
        "database": db_status,
        "groq": {"total_keys": len(settings.groq_api_keys), "keys": groq_keys},
        "config": config_info,
    }


@router.get("/baselinker-sync")
async def get_baselinker_sync_log(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Recent BaseLinker sync entries — shows what orders were synced or failed.

    WHY: Admin needs visibility into BOL→BaseLinker pipeline without SSH.
    """
    rows = db.execute(text("""
        SELECT id, bol_order_id, baselinker_order_id, status, error_message, created_at
        FROM baselinker_sync_log
        ORDER BY created_at DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    # WHY: Single query with FILTER instead of 3 separate COUNT queries
    counts = db.execute(text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'synced') AS synced,
            COUNT(*) FILTER (WHERE status = 'error') AS errors
        FROM baselinker_sync_log
    """)).fetchone()
    total, synced, errors = counts[0], counts[1], counts[2]

    return {
        "enabled": bool(settings.baselinker_api_token),
        "totals": {"total": total, "synced": synced, "errors": errors},
        "items": [
            {
                "id": row[0],
                "bol_order_id": row[1],
                "baselinker_order_id": row[2],
                "status": row[3],
                "error_message": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            }
            for row in rows
        ],
    }


@router.post("/baselinker-sync/trigger")
async def trigger_baselinker_sync(
    _admin: str = Depends(require_admin),
):
    """Manually trigger BOL→BaseLinker sync cycle.

    WHY: For testing and debugging — don't wait 15 min for cron.
    """
    if not settings.baselinker_api_token:
        raise HTTPException(status_code=400, detail="BASELINKER_API_TOKEN not configured")

    from database import SessionLocal
    from services.baselinker_sync import sync_bol_orders
    result = await sync_bol_orders(SessionLocal)
    return result
