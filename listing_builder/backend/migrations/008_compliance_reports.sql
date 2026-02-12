-- backend/migrations/008_compliance_reports.sql
-- Purpose: Create compliance report tables (matching models/compliance.py)
-- NOT for: Monitoring alerts or tracked products (those are in 002)

-- ============================================
-- COMPLIANCE REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS compliance_reports (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    marketplace VARCHAR(50) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    total_products INTEGER DEFAULT 0,
    compliant_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    overall_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_reports_marketplace ON compliance_reports(marketplace);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_created ON compliance_reports(created_at DESC);


-- ============================================
-- COMPLIANCE REPORT ITEMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS compliance_report_items (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    report_id VARCHAR(36) NOT NULL REFERENCES compliance_reports(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    sku VARCHAR(500) DEFAULT '',
    product_title TEXT DEFAULT '',
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'compliant',
    issues JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_items_report ON compliance_report_items(report_id);
CREATE INDEX IF NOT EXISTS idx_compliance_items_status ON compliance_report_items(compliance_status);
