-- backend/migrations/009_user_settings.sql
-- Purpose: Persist user settings to DB instead of in-memory dict
-- NOT for: App config or env vars (those stay in config.py)

CREATE TABLE IF NOT EXISTS user_settings (
    user_id VARCHAR(100) PRIMARY KEY DEFAULT 'default',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
