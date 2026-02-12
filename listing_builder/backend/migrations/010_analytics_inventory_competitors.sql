-- /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/migrations/010_analytics_inventory_competitors.sql
-- Purpose: Analytics dashboard tables for inventory, competitors, and revenue tracking
-- NOT for: Historical archival (uses current state snapshots)

-- ============================================================================
-- 1. INVENTORY ITEMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    product_title TEXT NOT NULL,
    marketplace VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    days_of_supply INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'in_stock',
    unit_cost FLOAT NOT NULL DEFAULT 0.0,
    total_value FLOAT NOT NULL DEFAULT 0.0,
    last_restocked TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inventory_marketplace ON inventory_items(marketplace);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory_items(status);
CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory_items(sku);

-- Seed inventory data (15 items across 5 marketplaces)
INSERT INTO inventory_items (sku, product_title, marketplace, quantity, reorder_point, days_of_supply, status, unit_cost, total_value, last_restocked)
VALUES
    -- Amazon items
    ('AMZ-001', 'Wireless Bluetooth Headphones Pro', 'Amazon', 342, 100, 45, 'in_stock', 22.50, 7695.00, NOW() - INTERVAL '10 days'),
    ('AMZ-002', 'USB-C Fast Charging Cable 6ft', 'Amazon', 89, 200, 12, 'low_stock', 3.20, 284.80, NOW() - INTERVAL '25 days'),
    ('AMZ-003', 'Portable Phone Charger 10000mAh', 'Amazon', 0, 50, 0, 'out_of_stock', 15.00, 0.00, NOW() - INTERVAL '45 days'),

    -- eBay items
    ('EBY-001', 'Vintage Leather Wallet Men', 'eBay', 156, 50, 62, 'in_stock', 12.00, 1872.00, NOW() - INTERVAL '5 days'),
    ('EBY-002', 'Stainless Steel Water Bottle 32oz', 'eBay', 23, 75, 8, 'low_stock', 8.50, 195.50, NOW() - INTERVAL '30 days'),
    ('EBY-003', 'Retro Sunglasses Unisex', 'eBay', 567, 100, 120, 'overstock', 4.75, 2693.25, NOW() - INTERVAL '2 days'),

    -- Walmart items
    ('WMT-001', 'Organic Cotton Bed Sheets Queen', 'Walmart', 201, 80, 38, 'in_stock', 18.00, 3618.00, NOW() - INTERVAL '15 days'),
    ('WMT-002', 'Non-Stick Frying Pan 12 inch', 'Walmart', 0, 60, 0, 'out_of_stock', 11.00, 0.00, NOW() - INTERVAL '50 days'),
    ('WMT-003', 'Kitchen Knife Set 8-Piece', 'Walmart', 78, 40, 30, 'in_stock', 25.00, 1950.00, NOW() - INTERVAL '8 days'),

    -- Shopify items
    ('SHP-001', 'Handmade Soy Candle Lavender', 'Shopify', 445, 100, 90, 'overstock', 6.50, 2892.50, NOW() - INTERVAL '3 days'),
    ('SHP-002', 'Minimalist Desk Organizer Wood', 'Shopify', 34, 30, 15, 'in_stock', 14.00, 476.00, NOW() - INTERVAL '20 days'),
    ('SHP-003', 'Macrame Plant Hanger Set of 3', 'Shopify', 12, 25, 5, 'low_stock', 7.00, 84.00, NOW() - INTERVAL '35 days'),

    -- Allegro items
    ('ALG-001', 'Plecak turystyczny 40L wodoodporny', 'Allegro', 88, 30, 44, 'in_stock', 45.00, 3960.00, NOW() - INTERVAL '12 days'),
    ('ALG-002', 'Zestaw narzedzi domowych 120 elementow', 'Allegro', 0, 20, 0, 'out_of_stock', 65.00, 0.00, NOW() - INTERVAL '60 days'),
    ('ALG-003', 'Lampa biurkowa LED regulowana', 'Allegro', 210, 50, 70, 'in_stock', 18.00, 3780.00, NOW() - INTERVAL '7 days')
ON CONFLICT (sku) DO NOTHING;

-- ============================================================================
-- 2. COMPETITORS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_name VARCHAR(200) NOT NULL,
    asin VARCHAR(50) NOT NULL,
    product_title TEXT NOT NULL,
    marketplace VARCHAR(50) NOT NULL,
    their_price FLOAT NOT NULL DEFAULT 0.0,
    our_price FLOAT NOT NULL DEFAULT 0.0,
    price_difference FLOAT NOT NULL DEFAULT 0.0,
    their_rating FLOAT NOT NULL DEFAULT 0.0,
    their_reviews_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'tied',
    last_checked TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(asin, marketplace)
);

CREATE INDEX IF NOT EXISTS idx_competitors_marketplace ON competitors(marketplace);
CREATE INDEX IF NOT EXISTS idx_competitors_status ON competitors(status);
CREATE INDEX IF NOT EXISTS idx_competitors_asin ON competitors(asin);

-- Seed competitor data (15 competitors across marketplaces)
INSERT INTO competitors (competitor_name, asin, product_title, marketplace, their_price, our_price, price_difference, their_rating, their_reviews_count, status, last_checked)
VALUES
    -- Amazon competitors
    ('TechAudio Inc', 'B09X1234AB', 'Wireless Bluetooth Headphones Pro', 'Amazon', 39.99, 44.99, 5.00, 4.6, 12847, 'winning', NOW() - INTERVAL '2 hours'),
    ('CableKing', 'B09X5678CD', 'USB-C Fast Charging Cable 6ft', 'Amazon', 12.99, 11.99, -1.00, 4.3, 8234, 'losing', NOW() - INTERVAL '1 hour'),
    ('PowerBank Pro', 'B09X9012EF', 'Portable Phone Charger 10000mAh', 'Amazon', 29.99, 29.99, 0.00, 4.7, 15632, 'tied', NOW() - INTERVAL '30 minutes'),

    -- eBay competitors
    ('Leather Goods Co', 'EBY-VLW-001', 'Vintage Leather Wallet Men', 'eBay', 24.99, 22.99, -2.00, 4.8, 3421, 'losing', NOW() - INTERVAL '3 hours'),
    ('HydroBottles', 'EBY-SWB-002', 'Stainless Steel Water Bottle 32oz', 'eBay', 18.99, 19.99, 1.00, 4.5, 2187, 'winning', NOW() - INTERVAL '4 hours'),
    ('RetroStyle Shop', 'EBY-RSU-003', 'Retro Sunglasses Unisex', 'eBay', 14.99, 14.99, 0.00, 4.2, 1654, 'tied', NOW() - INTERVAL '1 hour'),

    -- Walmart competitors
    ('OrganicHome', 'WMT-OCB-001', 'Organic Cotton Bed Sheets Queen', 'Walmart', 34.99, 32.99, -2.00, 4.6, 5432, 'losing', NOW() - INTERVAL '5 hours'),
    ('KitchenPro', 'WMT-NSF-002', 'Non-Stick Frying Pan 12 inch', 'Walmart', 21.99, 19.99, -2.00, 4.4, 3876, 'losing', NOW() - INTERVAL '2 hours'),
    ('ChefEssentials', 'WMT-KKS-003', 'Kitchen Knife Set 8-Piece', 'Walmart', 49.99, 54.99, 5.00, 4.7, 6234, 'winning', NOW() - INTERVAL '1 hour'),

    -- Shopify competitors
    ('Artisan Candles', 'SHP-HSC-001', 'Handmade Soy Candle Lavender', 'Shopify', 16.99, 15.99, -1.00, 4.9, 987, 'losing', NOW() - INTERVAL '6 hours'),
    ('Wood Workshop', 'SHP-MDO-002', 'Minimalist Desk Organizer Wood', 'Shopify', 28.99, 28.99, 0.00, 4.5, 654, 'tied', NOW() - INTERVAL '3 hours'),
    ('Boho Decor', 'SHP-MPH-003', 'Macrame Plant Hanger Set of 3', 'Shopify', 19.99, 22.99, 3.00, 4.3, 432, 'winning', NOW() - INTERVAL '4 hours'),

    -- Allegro competitors
    ('Outdoor Gear PL', 'ALG-PT40-001', 'Plecak turystyczny 40L wodoodporny', 'Allegro', 189.99, 179.99, -10.00, 4.6, 2341, 'losing', NOW() - INTERVAL '2 hours'),
    ('Narzedzia Domowe', 'ALG-ZND-002', 'Zestaw narzedzi domowych 120 elementow', 'Allegro', 249.99, 259.99, 10.00, 4.4, 1876, 'winning', NOW() - INTERVAL '5 hours'),
    ('LED Oswietlenie', 'ALG-LBL-003', 'Lampa biurkowa LED regulowana', 'Allegro', 79.99, 79.99, 0.00, 4.7, 3254, 'tied', NOW() - INTERVAL '1 hour')
ON CONFLICT (asin, marketplace) DO NOTHING;

-- ============================================================================
-- 3. REVENUE DATA TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS revenue_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace VARCHAR(50) NOT NULL,
    month VARCHAR(20) NOT NULL,
    revenue FLOAT NOT NULL DEFAULT 0.0,
    orders INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_revenue_marketplace ON revenue_data(marketplace);
CREATE INDEX IF NOT EXISTS idx_revenue_month ON revenue_data(month);

-- Seed revenue data (6 months × 5 marketplaces = 30 rows)
-- Distribution: Amazon 42.3%, eBay 18%, Walmart 20.6%, Shopify 11.4%, Allegro 7.7%
-- Base monthly revenue: ~$120,000 total with seasonal variation

INSERT INTO revenue_data (marketplace, month, revenue, orders)
VALUES
    -- September 2025 (lower month, ~$100k total)
    ('Amazon', 'Sep 2025', 42300.00, 1847),
    ('eBay', 'Sep 2025', 18000.00, 945),
    ('Walmart', 'Sep 2025', 20600.00, 1124),
    ('Shopify', 'Sep 2025', 11400.00, 687),
    ('Allegro', 'Sep 2025', 7700.00, 423),

    -- October 2025 (growing, ~$115k total)
    ('Amazon', 'Oct 2025', 48645.00, 2124),
    ('eBay', 'Oct 2025', 20700.00, 1086),
    ('Walmart', 'Oct 2025', 23690.00, 1292),
    ('Shopify', 'Oct 2025', 13110.00, 790),
    ('Allegro', 'Oct 2025', 8855.00, 486),

    -- November 2025 (holiday spike, ~$145k total)
    ('Amazon', 'Nov 2025', 61335.00, 2678),
    ('eBay', 'Nov 2025', 26100.00, 1369),
    ('Walmart', 'Nov 2025', 29870.00, 1629),
    ('Shopify', 'Nov 2025', 16530.00, 996),
    ('Allegro', 'Nov 2025', 11165.00, 613),

    -- December 2025 (peak, ~$180k total)
    ('Amazon', 'Dec 2025', 76140.00, 3324),
    ('eBay', 'Dec 2025', 32400.00, 1700),
    ('Walmart', 'Dec 2025', 37080.00, 2023),
    ('Shopify', 'Dec 2025', 20520.00, 1237),
    ('Allegro', 'Dec 2025', 13860.00, 761),

    -- January 2026 (post-holiday drop, ~$95k total)
    ('Amazon', 'Jan 2026', 40185.00, 1754),
    ('eBay', 'Jan 2026', 17100.00, 897),
    ('Walmart', 'Jan 2026', 19570.00, 1068),
    ('Shopify', 'Jan 2026', 10830.00, 652),
    ('Allegro', 'Jan 2026', 7315.00, 402),

    -- February 2026 (recovery, ~$125k total)
    ('Amazon', 'Feb 2026', 52875.00, 2309),
    ('eBay', 'Feb 2026', 22500.00, 1180),
    ('Walmart', 'Feb 2026', 25750.00, 1405),
    ('Shopify', 'Feb 2026', 14250.00, 859),
    ('Allegro', 'Feb 2026', 9625.00, 529)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE inventory_items IS 'Current inventory snapshot across all marketplaces with reorder alerts';
COMMENT ON TABLE competitors IS 'Competitor price tracking with ASIN-level comparison';
COMMENT ON TABLE revenue_data IS 'Monthly revenue aggregates by marketplace for analytics dashboard';

COMMENT ON COLUMN inventory_items.days_of_supply IS 'Calculated days until stockout at current sales velocity';
COMMENT ON COLUMN inventory_items.status IS 'Stock status: in_stock, low_stock, out_of_stock, overstock';
COMMENT ON COLUMN competitors.price_difference IS 'Positive = we are more expensive, negative = we are cheaper';
COMMENT ON COLUMN competitors.status IS 'Price position: winning (cheaper), losing (more expensive), tied (equal)';
