-- backend/migrations/006_listings_keywords.sql
-- Purpose: Create DB-backed tables for listings and tracked keywords (replacing mock data)
-- NOT for: Monitoring/alert tables (those are in 002)

-- ============================================
-- LISTINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    marketplace VARCHAR(50) NOT NULL,
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'compliant',
    issues_count INTEGER DEFAULT 0,
    last_checked TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_listings_marketplace ON listings(marketplace);
CREATE INDEX IF NOT EXISTS idx_listings_compliance ON listings(compliance_status);
CREATE INDEX IF NOT EXISTS idx_listings_sku ON listings(sku);


-- ============================================
-- TRACKED KEYWORDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tracked_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL,
    search_volume INTEGER DEFAULT 0,
    current_rank INTEGER,
    marketplace VARCHAR(50) NOT NULL,
    trend VARCHAR(10) DEFAULT 'stable',
    relevance_score INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(keyword, marketplace)
);

CREATE INDEX IF NOT EXISTS idx_tkw_marketplace ON tracked_keywords(marketplace);
CREATE INDEX IF NOT EXISTS idx_tkw_rank ON tracked_keywords(current_rank);
CREATE INDEX IF NOT EXISTS idx_tkw_keyword ON tracked_keywords(keyword);


-- ============================================
-- SEED DATA — Listings
-- ============================================
INSERT INTO listings (sku, title, marketplace, compliance_status, issues_count, last_checked)
VALUES
    ('AMZ-001', 'Wireless Bluetooth Headphones Pro', 'Amazon', 'compliant', 0, '2026-02-01T10:30:00Z'),
    ('AMZ-002', 'USB-C Fast Charging Cable 6ft', 'Amazon', 'warning', 2, '2026-02-01T09:15:00Z'),
    ('EBY-001', 'Vintage Leather Wallet Men', 'eBay', 'compliant', 0, '2026-02-01T08:00:00Z'),
    ('EBY-002', 'Stainless Steel Water Bottle 32oz', 'eBay', 'suppressed', 3, '2026-01-31T22:45:00Z'),
    ('WMT-001', 'Organic Cotton Bed Sheets Queen', 'Walmart', 'compliant', 0, '2026-02-01T11:00:00Z'),
    ('WMT-002', 'Non-Stick Frying Pan 12 inch', 'Walmart', 'blocked', 5, '2026-01-31T18:30:00Z'),
    ('SHP-001', 'Handmade Soy Candle Lavender', 'Shopify', 'compliant', 0, '2026-02-01T07:20:00Z'),
    ('SHP-002', 'Minimalist Desk Organizer Wood', 'Shopify', 'warning', 1, '2026-02-01T06:45:00Z'),
    ('ALG-001', 'Plecak turystyczny 40L wodoodporny', 'Allegro', 'compliant', 0, '2026-02-01T12:00:00Z'),
    ('ALG-002', 'Zestaw narzedzi domowych 120 elementow', 'Allegro', 'warning', 1, '2026-01-31T20:10:00Z')
ON CONFLICT (sku) DO NOTHING;


-- ============================================
-- SEED DATA — Tracked Keywords
-- ============================================
INSERT INTO tracked_keywords (keyword, search_volume, current_rank, marketplace, trend, relevance_score, last_updated)
VALUES
    ('wireless headphones', 245000, 3, 'Amazon', 'up', 95, '2026-02-01T10:00:00Z'),
    ('bluetooth earbuds', 189000, 7, 'Amazon', 'up', 92, '2026-02-01T10:00:00Z'),
    ('usb c cable', 320000, 12, 'Amazon', 'stable', 88, '2026-02-01T10:00:00Z'),
    ('leather wallet', 98000, 5, 'eBay', 'down', 90, '2026-02-01T08:30:00Z'),
    ('mens wallet bifold', 54000, 2, 'eBay', 'up', 85, '2026-02-01T08:30:00Z'),
    ('water bottle stainless', 167000, NULL, 'eBay', 'stable', 78, '2026-02-01T08:30:00Z'),
    ('bed sheets queen', 210000, 8, 'Walmart', 'up', 91, '2026-02-01T11:00:00Z'),
    ('organic cotton sheets', 87000, 15, 'Walmart', 'stable', 82, '2026-02-01T11:00:00Z'),
    ('nonstick frying pan', 143000, 22, 'Walmart', 'down', 75, '2026-02-01T11:00:00Z'),
    ('soy candle lavender', 34000, 1, 'Shopify', 'up', 97, '2026-02-01T07:00:00Z'),
    ('handmade candles', 78000, 4, 'Shopify', 'stable', 89, '2026-02-01T07:00:00Z'),
    ('desk organizer wood', 45000, NULL, 'Shopify', 'down', 72, '2026-02-01T07:00:00Z'),
    ('plecak turystyczny', 28000, 6, 'Allegro', 'up', 94, '2026-02-01T12:00:00Z'),
    ('plecak wodoodporny', 15000, 9, 'Allegro', 'stable', 86, '2026-02-01T12:00:00Z'),
    ('zestaw narzedzi', 42000, 18, 'Allegro', 'down', 70, '2026-02-01T12:00:00Z')
ON CONFLICT (keyword, marketplace) DO NOTHING;
