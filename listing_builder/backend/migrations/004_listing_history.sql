-- backend/migrations/004_listing_history.sql
-- Purpose: Self-learning store for high-quality listings (Ranking Juice >= 75)
-- NOT for: General optimization history (that's optimization_runs)

CREATE TABLE IF NOT EXISTS listing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand TEXT NOT NULL,
    marketplace TEXT NOT NULL,
    product_title TEXT NOT NULL,
    title TEXT NOT NULL,
    bullets JSONB NOT NULL,
    description TEXT NOT NULL,
    backend_keywords TEXT NOT NULL,
    ranking_juice REAL NOT NULL,
    grade TEXT NOT NULL,
    keyword_count INT NOT NULL,
    user_rating INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_listing_history_rj ON listing_history (ranking_juice DESC);
CREATE INDEX idx_listing_history_marketplace ON listing_history (marketplace);
