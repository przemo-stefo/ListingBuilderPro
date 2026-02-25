-- backend/migrations/017_admin_premium_accounts.sql
-- Purpose: Grant lifetime premium to admin accounts (Mateusz, Bartek)
-- WHY: Spotkanie 24.02 — admin accounts = premium without Stripe payment
-- NOTE: Prefer using POST /api/admin/grant-premium endpoint instead of raw SQL

-- Mateusz Grzywnowicz (VIAREGIA.ONLINE owner)
INSERT INTO premium_licenses (email, license_key, plan_type, status, expires_at)
SELECT 'mateuszgrzywnowicz@gmail.com', encode(gen_random_bytes(32), 'base64'), 'lifetime', 'active', NULL
WHERE NOT EXISTS (
    SELECT 1 FROM premium_licenses WHERE email = 'mateuszgrzywnowicz@gmail.com' AND status = 'active'
);

-- Bartosz Siomra-Janicki (współpracownik, admin)
INSERT INTO premium_licenses (email, license_key, plan_type, status, expires_at)
SELECT 'bartosz.siomra-janicki@octosello.com', encode(gen_random_bytes(32), 'base64'), 'lifetime', 'active', NULL
WHERE NOT EXISTS (
    SELECT 1 FROM premium_licenses WHERE email = 'bartosz.siomra-janicki@octosello.com' AND status = 'active'
);
