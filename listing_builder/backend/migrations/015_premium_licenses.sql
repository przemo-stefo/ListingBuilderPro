-- backend/migrations/015_premium_licenses.sql
-- Purpose: License key table for Stripe Premium plans (lifetime + monthly)
-- NOT for: Subscription-based billing (that's 012_subscriptions.sql)

CREATE TABLE IF NOT EXISTS premium_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    license_key TEXT NOT NULL UNIQUE,
    stripe_customer_id TEXT,
    stripe_checkout_session_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    plan_type TEXT NOT NULL CHECK (plan_type IN ('lifetime', 'monthly')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- WHY: Fast license validation on every API request
CREATE INDEX IF NOT EXISTS idx_premium_licenses_key ON premium_licenses (license_key);
-- WHY: License recovery by email
CREATE INDEX IF NOT EXISTS idx_premium_licenses_email ON premium_licenses (email);
