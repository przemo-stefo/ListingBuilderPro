-- Migration 011: EPR (Extended Producer Responsibility) reports from Amazon SP-API
-- Purpose: Store EPR compliance reports (WEEE, packaging, batteries) fetched via SP-API

CREATE TABLE IF NOT EXISTS epr_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type TEXT NOT NULL,
    marketplace_id TEXT NOT NULL DEFAULT 'A1PA6795UKMFR9',
    status TEXT NOT NULL DEFAULT 'pending',
    sp_api_report_id TEXT,
    row_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS epr_report_rows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES epr_reports(id) ON DELETE CASCADE,
    asin TEXT,
    marketplace TEXT,
    epr_category TEXT,
    registration_number TEXT,
    paper_kg NUMERIC(10,4) DEFAULT 0,
    glass_kg NUMERIC(10,4) DEFAULT 0,
    aluminum_kg NUMERIC(10,4) DEFAULT 0,
    steel_kg NUMERIC(10,4) DEFAULT 0,
    plastic_kg NUMERIC(10,4) DEFAULT 0,
    wood_kg NUMERIC(10,4) DEFAULT 0,
    units_sold INTEGER DEFAULT 0,
    reporting_period TEXT
);

CREATE INDEX IF NOT EXISTS idx_epr_rows_report ON epr_report_rows(report_id);
CREATE INDEX IF NOT EXISTS idx_epr_reports_status ON epr_reports(status);
