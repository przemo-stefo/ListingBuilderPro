# backend/api/admin_routes.py
# Purpose: Admin-only endpoints — cost dashboard, usage stats for Mateusz
# NOT for: User-facing features or settings (those are in settings_routes.py)

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/costs")
async def get_cost_dashboard(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Cost dashboard — total spend, per-provider breakdown, daily trend.

    WHY: Mateusz needs to see how much API usage costs so he can control expenses.
    Data comes from optimization_runs.trace_data (already tracked per run).
    """
    # WHY: Cap at 365 days max to prevent huge queries
    days = min(days, 365)

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
