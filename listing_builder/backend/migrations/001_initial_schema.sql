-- /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/migrations/001_initial_schema.sql
-- Purpose: Initial database schema for Marketplace Listing Automation
-- NOT for: Application logic or configuration

-- Enable UUID extension (optional, if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- PRODUCTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,

    -- Source data
    source_platform VARCHAR(50) DEFAULT 'allegro',
    source_id VARCHAR(255) NOT NULL,
    source_url TEXT,

    -- Product details
    title_original TEXT NOT NULL,
    title_optimized TEXT,
    description_original TEXT,
    description_optimized TEXT,
    category VARCHAR(255),
    brand VARCHAR(255),

    -- Pricing
    price FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'PLN',

    -- Media and attributes (JSONB for performance)
    images JSONB DEFAULT '[]'::jsonb,
    attributes JSONB DEFAULT '{}'::jsonb,

    -- AI optimization
    optimized_data JSONB,
    optimization_score FLOAT,

    -- Status
    status VARCHAR(20) DEFAULT 'imported',

    -- Marketplace data
    marketplace_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Unique constraint on source
    CONSTRAINT unique_source_product UNIQUE(source_platform, source_id)
);

-- Indexes for products
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_source_platform ON products(source_platform);
CREATE INDEX idx_products_source_id ON products(source_id);
CREATE INDEX idx_products_created_at ON products(created_at DESC);


-- ============================================
-- IMPORT JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS import_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) DEFAULT 'allegro',
    status VARCHAR(20) DEFAULT 'pending',

    -- Stats
    total_products INT DEFAULT 0,
    processed_products INT DEFAULT 0,
    failed_products INT DEFAULT 0,

    -- Data
    raw_data JSONB,
    error_log JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_created_at ON import_jobs(created_at DESC);


-- ============================================
-- BULK JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS bulk_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    target_marketplace VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',

    -- Product tracking
    product_ids JSONB DEFAULT '[]'::jsonb,
    total_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,

    -- Results
    results JSONB DEFAULT '[]'::jsonb,
    error_log JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_bulk_jobs_status ON bulk_jobs(status);
CREATE INDEX idx_bulk_jobs_type ON bulk_jobs(job_type);
CREATE INDEX idx_bulk_jobs_marketplace ON bulk_jobs(target_marketplace);


-- ============================================
-- SYNC LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    marketplace VARCHAR(50) NOT NULL,
    sync_type VARCHAR(50) NOT NULL,

    -- Changes
    old_value JSONB,
    new_value JSONB,

    -- Status
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,

    -- Timestamp
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sync_logs_product_id ON sync_logs(product_id);
CREATE INDEX idx_sync_logs_marketplace ON sync_logs(marketplace);
CREATE INDEX idx_sync_logs_synced_at ON sync_logs(synced_at DESC);


-- ============================================
-- WEBHOOKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,

    -- Request data
    payload JSONB NOT NULL,
    headers JSONB,

    -- Processing
    processed INT DEFAULT 0,
    error_message TEXT,

    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_webhooks_source ON webhooks(source);
CREATE INDEX idx_webhooks_processed ON webhooks(processed);
CREATE INDEX idx_webhooks_received_at ON webhooks(received_at DESC);


-- ============================================
-- ROW LEVEL SECURITY (RLS) - Optional
-- ============================================
-- Enable RLS on tables (if using Supabase Auth)
-- ALTER TABLE products ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE import_jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE bulk_jobs ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow authenticated users to read all products
-- CREATE POLICY "Allow authenticated read" ON products
--     FOR SELECT
--     USING (auth.role() = 'authenticated');


-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products table
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- SEED DATA (Optional - for testing)
-- ============================================

-- Insert a test product
INSERT INTO products (
    source_platform,
    source_id,
    source_url,
    title_original,
    description_original,
    category,
    brand,
    price,
    currency,
    images,
    attributes,
    status
) VALUES (
    'allegro',
    'TEST-001',
    'https://allegro.pl/offer/test-001',
    'Test Product - Premium Quality Widget',
    'This is a test product for development purposes.',
    'Electronics',
    'TestBrand',
    99.99,
    'PLN',
    '["https://example.com/image1.jpg", "https://example.com/image2.jpg"]'::jsonb,
    '{"color": "black", "size": "M"}'::jsonb,
    'imported'
) ON CONFLICT (source_platform, source_id) DO NOTHING;


-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check all tables exist
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check products count
-- SELECT COUNT(*) FROM products;
