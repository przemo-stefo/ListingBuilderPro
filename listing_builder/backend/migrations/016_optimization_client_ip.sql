-- backend/migrations/016_optimization_client_ip.sql
-- Purpose: Add client_ip column for per-IP free tier limit enforcement
-- NOT for: License key validation (that's premium_licenses table)

ALTER TABLE optimization_runs ADD COLUMN IF NOT EXISTS client_ip VARCHAR(45);
