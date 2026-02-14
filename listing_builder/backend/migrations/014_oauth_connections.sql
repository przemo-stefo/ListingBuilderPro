-- backend/migrations/014_oauth_connections.sql
-- Purpose: Store per-seller OAuth connections (Amazon SP-API, Allegro, etc.)
-- NOT for: App-level API keys (those are env vars)

CREATE TABLE IF NOT EXISTS oauth_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default',
    marketplace TEXT NOT NULL,             -- amazon, allegro, kaufland
    status TEXT NOT NULL DEFAULT 'pending', -- pending, active, expired, revoked
    -- WHY separate fields: different providers use different token schemas
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    seller_id TEXT,                        -- Amazon merchant_id / Allegro user_id
    seller_name TEXT,                      -- Display name
    marketplace_ids TEXT[],               -- Amazon: ['A1PA6795UKMFR9'] etc.
    scopes TEXT,                           -- Granted OAuth scopes
    raw_data JSONB,                        -- Full provider response for debugging
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_user_marketplace
    ON oauth_connections(user_id, marketplace);
CREATE INDEX IF NOT EXISTS idx_oauth_marketplace
    ON oauth_connections(marketplace);
