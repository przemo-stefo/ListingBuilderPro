-- /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/migrations/002_alert_tables.sql
-- Purpose: Monitoring & alerts tables for Compliance Guard
-- NOT for: Application logic or compliance report tables (see 001_initial_schema.sql)

-- ============================================
-- TRACKED PRODUCTS TABLE
-- Products being monitored across marketplaces
-- ============================================
CREATE TABLE IF NOT EXISTS tracked_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    marketplace TEXT NOT NULL,            -- allegro, amazon, kaufland, ebay
    product_id TEXT NOT NULL,             -- ASIN, offer ID, EAN, etc.
    product_url TEXT,
    product_title TEXT,
    poll_interval_hours INT DEFAULT 6,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, marketplace, product_id)
);

CREATE INDEX IF NOT EXISTS idx_tracked_user ON tracked_products(user_id);
CREATE INDEX IF NOT EXISTS idx_tracked_marketplace ON tracked_products(marketplace);
CREATE INDEX IF NOT EXISTS idx_tracked_enabled ON tracked_products(enabled) WHERE enabled = true;


-- ============================================
-- MONITORING SNAPSHOTS TABLE
-- Price/stock/status snapshots captured by scheduler
-- ============================================
CREATE TABLE IF NOT EXISTS monitoring_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracked_product_id UUID REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace TEXT NOT NULL,
    product_id TEXT NOT NULL,
    ean TEXT,
    snapshot_data JSONB NOT NULL,          -- {price, currency, stock, buy_box_owner, listing_active, ...}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_tracked ON monitoring_snapshots(tracked_product_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_product ON monitoring_snapshots(marketplace, product_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_created ON monitoring_snapshots(created_at DESC);


-- ============================================
-- ALERT CONFIGS TABLE
-- User-defined alert rules (what to monitor, thresholds)
-- ============================================
CREATE TABLE IF NOT EXISTS alert_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,              -- price_change, buy_box_lost, low_stock, listing_deactivated
    name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    threshold FLOAT,                       -- e.g. 5.0 for 5% price change
    marketplace TEXT,                      -- NULL = all marketplaces
    email TEXT,
    webhook_url TEXT,
    cooldown_minutes INT DEFAULT 60,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_configs_user ON alert_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_configs_type ON alert_configs(alert_type);


-- ============================================
-- ALERTS TABLE
-- Triggered alert history
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES alert_configs(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,                -- info, warning, critical
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_config ON alerts(config_id);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);


-- ============================================
-- VERIFICATION
-- ============================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('tracked_products', 'monitoring_snapshots', 'alert_configs', 'alerts');
