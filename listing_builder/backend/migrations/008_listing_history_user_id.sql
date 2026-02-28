-- backend/migrations/008_listing_history_user_id.sql
-- Purpose: Add user_id to listing_history for tenant isolation (SECURITY: cross-tenant data leak fix)
-- NOT for: Other tables — only listing_history

-- WHY: Without user_id, all users' listings are shared as few-shot examples (data leak)
ALTER TABLE listing_history ADD COLUMN IF NOT EXISTS user_id TEXT;

-- WHY: Backfill existing rows from optimization_runs where possible
UPDATE listing_history lh
SET user_id = sub.user_id
FROM (
    SELECT DISTINCT ON (or2.response_data->>'listing_history_id')
        or2.response_data->>'listing_history_id' AS lh_id,
        or2.user_id
    FROM optimization_runs or2
    WHERE or2.response_data->>'listing_history_id' IS NOT NULL
) sub
WHERE lh.id::text = sub.lh_id AND lh.user_id IS NULL;

-- WHY: Index for filtered queries — get_past_successes filters by user_id + marketplace
CREATE INDEX IF NOT EXISTS idx_listing_history_user_marketplace
    ON listing_history (user_id, marketplace, ranking_juice DESC);
