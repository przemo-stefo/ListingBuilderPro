-- backend/migrations/018_hash_client_ips.sql
-- Purpose: GDPR — replace raw IP addresses with salted SHA256 hashes
-- NOT for: Changing rate limiting logic (hash comparison still works)

-- WHY: Raw IPs are PII under GDPR. After this migration, only hashed IPs
-- remain in the DB. Rate limiting still works because the same IP always
-- produces the same hash (salted with api_secret_key prefix).
--
-- NOTE: Run this AFTER deploying the new code that writes hashed IPs.
-- Old raw IPs are replaced with a SHA256 hash using the DB-side salt.
-- The salt must match the Python hash_ip() function in utils/privacy.py.

-- Step 1: Hash all existing raw client_ip values that look like IPs (contain dots or colons)
-- The salt prefix must match settings.api_secret_key[:16] — set it below before running!
-- REPLACE 'YOUR_SALT_HERE' with the first 16 chars of your API_SECRET_KEY env var.

-- UPDATE optimization_runs
-- SET client_ip = LEFT(encode(sha256(('YOUR_SALT_HERE:' || client_ip)::bytea), 'hex'), 32)
-- WHERE client_ip IS NOT NULL
--   AND client_ip ~ '^[0-9a-fA-F.:]+$';

-- IMPORTANT: Uncomment and set salt before running on production.
-- After running, verify: SELECT client_ip FROM optimization_runs LIMIT 5;
-- Should show 32-char hex strings, not IP addresses.
