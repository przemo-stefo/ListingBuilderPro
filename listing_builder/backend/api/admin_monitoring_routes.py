# backend/api/admin_monitoring_routes.py
# Purpose: Admin monitoring endpoints — system health, activity, costs, OAuth, BaseLinker sync
# NOT for: License management or admin overview (those are in admin_routes.py)

import asyncio
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine
from api.dependencies import require_admin
from config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/admin", tags=["Admin Monitoring"])


@router.get("/costs")
async def get_cost_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """Cost dashboard — total spend, per-provider breakdown, daily trend.

    WHY: Mateusz needs to see how much API usage costs so he can control expenses.
    """

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
            {"model": row[0], "runs": row[1], "tokens": int(row[2]),
             "cost_usd": round(float(row[3]), 4)}
            for row in by_provider
        ],
        "daily": [
            {"date": row[0].isoformat(), "runs": row[1], "tokens": int(row[2]),
             "cost_usd": round(float(row[3]), 4)}
            for row in daily
        ],
    }


@router.get("/oauth-connections")
async def get_oauth_connections(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """OAuth connections grouped by user — which marketplaces each user connected."""
    rows = db.execute(text("""
        SELECT user_id, marketplace, status, seller_name, created_at
        FROM oauth_connections
        ORDER BY created_at DESC
    """)).fetchall()

    return {
        "items": [
            {
                "user_id": row[0], "marketplace": row[1], "status": row[2],
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
    """Recent activity — optimizations, imports, compliance reports."""

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
            {"id": row[0], "title": row[1], "marketplace": row[2], "mode": row[3],
             "client_ip": row[4], "created_at": row[5].isoformat() if row[5] else None}
            for row in optimizations
        ],
        "imports": [
            {"id": row[0], "source": row[1], "status": str(row[2]),
             "total_products": row[3], "created_at": row[4].isoformat() if row[4] else None}
            for row in imports
        ],
        "compliance_reports": [
            {"id": row[0], "marketplace": row[1], "total_products": row[2],
             "overall_score": round(float(row[3]), 1) if row[3] else 0,
             "created_at": row[4].isoformat() if row[4] else None}
            for row in reports
        ],
    }


@router.get("/system")
async def get_system_status(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    """System health — DB, Groq keys, config."""

    try:
        pool = engine.pool
        db_status = {"status": "connected", "pool_size": pool.size(), "checked_out": pool.checkedout()}
    except Exception as e:
        logger.error("db_pool_check_failed", error=str(e))
        db_status = {"status": "error", "error": "connection_failed"}

    # WHY: asyncio.to_thread because Groq SDK is synchronous — would block event loop
    def _check_groq_keys():
        results = []
        for i, key in enumerate(settings.groq_api_keys):
            try:
                from groq import Groq
                client = Groq(api_key=key, timeout=5.0)
                client.models.list()
                results.append({"index": i + 1, "status": "ok", "error": None})
            except Exception as e:
                logger.error("groq_key_check_failed", index=i + 1, error=str(e))
                results.append({"index": i + 1, "status": "error", "error": "validation_failed"})
        return results

    groq_keys = await asyncio.to_thread(_check_groq_keys)

    config_info = {
        "groq_model": settings.groq_model,
        "admin_emails_count": len(settings.admin_emails_list),
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
    """Recent BaseLinker sync entries — shows what orders were synced or failed."""
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

    return {
        "enabled": bool(settings.baselinker_api_token),
        "totals": {"total": counts[0], "synced": counts[1], "errors": counts[2]},
        "items": [
            {"id": row[0], "bol_order_id": row[1], "baselinker_order_id": row[2],
             "status": row[3], "error_message": row[4],
             "created_at": row[5].isoformat() if row[5] else None}
            for row in rows
        ],
    }


@router.post("/baselinker-sync/trigger")
async def trigger_baselinker_sync(
    _admin: str = Depends(require_admin),
):
    """Manually trigger BOL→BaseLinker sync cycle."""
    if not settings.baselinker_api_token:
        raise HTTPException(status_code=400, detail="BASELINKER_API_TOKEN not configured")

    from database import SessionLocal
    from services.baselinker_sync import sync_bol_orders
    result = await sync_bol_orders(SessionLocal)
    # WHY: Don't leak raw exception strings — keep details in server logs only
    if "fatal" in result:
        result["fatal"] = "sync_failed"
    return result
