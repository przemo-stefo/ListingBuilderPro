# backend/services/trace_service.py
# Purpose: Lightweight tracing for optimizer — measures latency, token usage, cost
# NOT for: Distributed tracing or external APM (no new dependencies)

import time
from datetime import datetime, timezone
from contextlib import contextmanager

# WHY: Groq llama-3.3-70b pricing per 1M tokens (as of 2026-02)
COST_PER_1M = {"prompt": 0.59, "completion": 0.79}


def new_trace(name: str) -> dict:
    """Start a new trace with a name and empty spans list."""
    return {
        "name": name,
        "start": time.monotonic(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "spans": [],
        "total_tokens": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
    }


@contextmanager
def span(trace: dict, name: str):
    """Context manager that measures wall-clock time for a step.

    Yields the span dict so callers can attach token usage via record_llm_usage.
    """
    s = {"name": name, "start": time.monotonic(), "error": None}
    try:
        yield s
    except Exception as exc:
        s["error"] = str(exc)
        raise
    finally:
        elapsed = time.monotonic() - s["start"]
        s["duration_ms"] = round(elapsed * 1000, 1)
        # WHY: Remove monotonic floats — not serializable / not useful in JSON
        del s["start"]
        trace["spans"].append(s)


def record_llm_usage(s: dict, usage: dict, accumulate: bool = False):
    """Attach token counts from a Groq response to a span.

    Args:
        s: The span dict (yielded by span context manager).
        usage: Dict with prompt_tokens, completion_tokens, total_tokens, model.
        accumulate: If True, add to existing token counts (for parallel calls in one span).
    """
    if accumulate and "tokens_in" in s:
        s["tokens_in"] += usage.get("prompt_tokens", 0)
        s["tokens_out"] += usage.get("completion_tokens", 0)
        s["tokens_total"] += usage.get("total_tokens", 0)
    else:
        s["tokens_in"] = usage.get("prompt_tokens", 0)
        s["tokens_out"] = usage.get("completion_tokens", 0)
        s["tokens_total"] = usage.get("total_tokens", 0)
        s["model"] = usage.get("model", "unknown")


def finalize_trace(trace: dict) -> dict:
    """Compute totals and estimated cost. Returns a clean dict for JSON storage."""
    total_ms = round((time.monotonic() - trace["start"]) * 1000, 1)

    prompt_tokens = 0
    completion_tokens = 0
    for s in trace["spans"]:
        prompt_tokens += s.get("tokens_in", 0)
        completion_tokens += s.get("tokens_out", 0)

    total_tokens = prompt_tokens + completion_tokens

    # WHY: Cost estimate helps track spend without external billing dashboards
    est_cost = (
        (prompt_tokens / 1_000_000) * COST_PER_1M["prompt"]
        + (completion_tokens / 1_000_000) * COST_PER_1M["completion"]
    )

    return {
        "name": trace["name"],
        "started_at": trace["started_at"],
        "total_duration_ms": total_ms,
        "total_tokens": total_tokens,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "estimated_cost_usd": round(est_cost, 6),
        "spans": trace["spans"],
    }
