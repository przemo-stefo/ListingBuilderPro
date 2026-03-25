-- 021_catalog_health.sql
-- Purpose: Tables for Catalog Health Check module (scan + issues)

CREATE TABLE IF NOT EXISTS catalog_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    marketplace TEXT NOT NULL DEFAULT 'DE',
    seller_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    progress JSONB DEFAULT '{"phase": "waiting", "percent": 0}',
    total_listings INT DEFAULT 0,
    issues_found INT DEFAULT 0,
    issues_fixed INT DEFAULT 0,
    scan_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS catalog_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES catalog_scans(id) ON DELETE CASCADE,
    asin TEXT,
    sku TEXT,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning',
    title TEXT NOT NULL,
    description TEXT,
    amazon_issue_code TEXT,
    fix_proposal JSONB,
    fix_status TEXT DEFAULT 'pending',
    fix_result JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_catalog_scans_user ON catalog_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_catalog_issues_scan ON catalog_issues(scan_id);
CREATE INDEX IF NOT EXISTS idx_catalog_issues_type ON catalog_issues(issue_type);
CREATE INDEX IF NOT EXISTS idx_catalog_issues_severity ON catalog_issues(severity);

ALTER TABLE catalog_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_issues ENABLE ROW LEVEL SECURITY;
