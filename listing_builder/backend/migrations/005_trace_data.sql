-- 005_trace_data.sql
-- Purpose: Add observability trace column to optimization_runs
-- WHY: Stores per-run token usage, latency per step, and estimated cost as JSONB

ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS trace_data JSONB;
