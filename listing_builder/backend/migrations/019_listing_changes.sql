-- migrations/019_listing_changes.sql
-- Purpose: Table for tracking field-level listing changes detected by SP-API polling
-- NOT for: Alert configs or snapshot data (those are in earlier migrations)

CREATE TABLE IF NOT EXISTS listing_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracked_product_id UUID REFERENCES tracked_products(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    marketplace VARCHAR(50) NOT NULL,
    product_id VARCHAR(500) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lc_user_product ON listing_changes(user_id, product_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_lc_tracked ON listing_changes(tracked_product_id);
