# Security Audit & Hardening — ListingBuilderPro

**Data:** 2026-02-14
**Audytor:** Claude Opus 4.6 (security-auditor agent)
**Scope:** Full backend (FastAPI) + frontend proxy (Next.js 14) + infra (Render/Vercel/Supabase)

---

## Architektura

- **Frontend:** Next.js 14 na Vercel → proxy `/api/proxy/[...path]` → backend (API key injected server-side)
- **Backend:** FastAPI + Groq LLM + Supabase PostgreSQL na Render (Docker)
- **Auth:** API key middleware (X-API-Key header) + license key system (X-License-Key)
- **Payments:** Stripe Checkout (hosted) — lifetime (149 PLN) + monthly (49 PLN/mies)
- **OAuth:** Amazon SP-API + Allegro OAuth2 flows
- **Monitoring:** APScheduler (allegro/ebay 6h, amazon/kaufland 4h)

---

## Naprawione (2026-02-14)

### CRITICAL — naprawione

| # | Problem | Plik | Commit |
|---|---------|------|--------|
| C1 | `.env` nie było w root `.gitignore` — ryzyko commit secretów | `.gitignore` | `66aeba3` |
| C2 | **SSRF w webhook_url alertów** — user mógł ustawić `http://169.254.169.254/` i backend robił fetch do AWS metadata | `schemas/monitoring.py`, `utils/url_validator.py` | `66aeba3` |
| C3 | **SSRF w product_url scrapera** — user mógł scrapować internal URLs | `schemas/monitoring.py`, `utils/url_validator.py` | `66aeba3` |
| C4 | **SSRF w /compliance/audit** — user-supplied URL bez walidacji domeny | `schemas/audit.py`, `utils/url_validator.py` | `66aeba3` + `36b4e86` |
| C5 | **`?unlock=premium` URL bypass** — każdy mógł dostać premium przez URL param | `TierProvider.tsx` | `deeab93` |
| C6 | **`?payment=success` zaufany bez weryfikacji** — frontend ustawiał premium bez sprawdzenia backendu | `TierProvider.tsx` | `deeab93` |
| C7 | **Brak server-side tier enforcement** — optimizer limit (3/dzień) był tylko na froncie (localStorage), ominięcie przez curl | `optimizer_routes.py` | `deeab93` |

### HIGH — naprawione

| # | Problem | Plik | Commit |
|---|---------|------|--------|
| H-fix1 | `stripe_customer_id` wyciekał w API response — internal Stripe ID | `schemas/subscription.py`, `stripe_routes.py` | `deeab93` |
| H-fix2 | Brak rate limit na `/stripe/status` | `stripe_routes.py` (30/min) | `deeab93` |
| H-fix3 | Brak rate limit na `/stripe/webhook` | `stripe_routes.py` (60/min) | `deeab93` |
| H-fix4 | `event_type` wyciekał w webhook response | `stripe_routes.py` | `deeab93` |

### MEDIUM — naprawione

| # | Problem | Plik | Commit |
|---|---------|------|--------|
| M1 | **Batch optimizer omijał tier limit** — 1 check na 50 produktów | `optimizer_routes.py` (`requested_count`) | `deeab93` + `66aeba3` |
| M2 | **`app_debug=True` domyślnie** — `/docs` widoczny jeśli env nie ustawiony | `config.py` (default `False`) | `66aeba3` |
| M3 | **Error message leaking** w `/compliance/audit` — `str(e)` do klienta | `compliance_routes.py` | `66aeba3` |
| M4 | **PATCH brakowało w CORS** — feedback endpoint mógł być blokowany | `main.py` | `deeab93` |

### Zmiany użytkownika (poza audytem)

| Zmiana | Plik |
|--------|------|
| Stripe: subscription → license key model (lifetime + monthly) | `config.py` |
| Tier check: Subscription query → `validate_license()` + per-IP daily limit | `optimizer_routes.py` |
| `client_ip` tracking na `OptimizationRun` | `optimizer_routes.py` |

---

## Otwarte — HIGH (do naprawy)

### H1. OAuth CSRF State w pamięci

**Pliki:** `backend/services/oauth_service.py:20`
**Problem:** `_pending_states` to Python dict w pamięci. Ginie przy restart serwera lub przy wielu workerach (Render może mieć >1 worker). Stare state nigdy nie są czyszczone (memory leak). Brak TTL — przechwycony state działa w nieskończoność.
**Fix:** Przenieść state do tabeli DB (`oauth_pending_states`) z `created_at` + `expires_at` (10 min). Cleanup w query (`WHERE expires_at < now()`).

### H2. OAuth error w redirect URL bez URL-encoding

**Pliki:** `backend/api/oauth_routes.py:81,114`
**Problem:** `result['error']` wstawiany bezpośrednio do redirect URL bez `quote()`. Może zawierać znaki specjalne, wyciekać do browser history, referrer headers, analytics.
**Fix:** `from urllib.parse import quote; f"...&msg={quote(result['error'])}"` lub lepiej: generic error code zamiast pełnego tekstu błędu.

### H3. Brak rate limitów na kosztowne endpointy

**Pliki i proponowane limity:**

| Endpoint | Plik | Proponowany limit |
|----------|------|-------------------|
| `GET /api/keepa/product` | `keepa_routes.py:12` | `5/minute` |
| `GET /api/keepa/products` (batch) | `keepa_routes.py:24` | `3/minute` |
| `GET /api/keepa/buybox` | `keepa_routes.py:40` | `5/minute` |
| `GET /api/keepa/tokens` | `keepa_routes.py:52` | `10/minute` |
| `GET /api/monitoring/tracked` | `monitoring_routes.py:76` | `30/minute` |
| `GET /api/monitoring/snapshots/{id}` | `monitoring_routes.py:127` | `30/minute` |
| `GET /api/monitoring/alerts` | `monitoring_routes.py:220` | `30/minute` |
| `GET /api/monitoring/alerts/configs` | `monitoring_routes.py:171` | `30/minute` |
| `GET /api/monitoring/dashboard` | `monitoring_routes.py:296` | `30/minute` |
| `GET /api/monitoring/status` | `monitoring_routes.py:247` | `30/minute` |
| `GET /api/knowledge/stats` | `knowledge_routes.py:78` | `20/minute` |
| `GET /api/optimizer/traces` | `optimizer_routes.py` | `20/minute` |
| `GET /api/optimizer/traces/stats` | `optimizer_routes.py` | `20/minute` |
| `GET /api/optimizer/history` | `optimizer_routes.py` | `30/minute` |

**Priorytet:** Keepa endpointy (kosztują tokeny API — pieniądze).

---

## Otwarte — MEDIUM (do naprawy później)

| # | Problem | Plik | Priorytet |
|---|---------|------|-----------|
| M-docker | Docker container działa jako root | `Dockerfile` | Ten tydzień |
| M-prompt | Prompt injection — brak `<user_input>` delimiter w LLM promptach | `optimizer_service.py` | Następny sprint |
| M-deps | Stare zależności (FastAPI 0.109, httpx 0.25, stripe 8.0) | `requirements.txt` | Następny sprint |
| M-oauth-enc | OAuth tokeny w DB jako plain text (bez encryption) | `oauth_connection.py` | Następny sprint |
| M-cors-dup | Podwójne CORS headers (CORSMiddleware + SecurityHeaders fallback) | `middleware/security.py:49` | Następny sprint |
| M-error-leak | `sp_api_auth.py:61` — `resp.text[:200]` w RuntimeError | `sp_api_auth.py` | Następny sprint |

---

## Otwarte — LOW

| # | Problem | Plik |
|---|---------|------|
| L1 | LinkedIn session cookie (`LINKEDIN_LI_AT`) w backend `.env` — nieużywany | `.env` |
| L2 | Render API key w `.env` — nie potrzebny w runtime | `.env` |
| L3 | `X-XSS-Protection` header deprecated | `middleware/security.py:44` |
| L4 | CSP `default-src 'self'` bezcelowy dla API | `middleware/security.py:45` |
| L5 | Brak `?sslmode=require` w DATABASE_URL | `.env` |
| L6 | `gcc` w Docker image (nie usunięty po build) | `Dockerfile` |
| L7 | Proxy nie sanityzuje `Content-Disposition` header | `proxy/[...path]/route.ts` |

---

## Co jest dobrze (pozytywne findings)

1. **API Key Auth** — `hmac.compare_digest` (timing-safe comparison)
2. **Proxy Allowlist** — explicit `ALLOWED_PATH_PREFIXES` na froncie
3. **Stripe Webhook** — signature verification z raw body (`construct_event()`)
4. **SQL** — parametryzowane query wszędzie (brak injection)
5. **Weak Secret Rejection** — `config.py` odrzuca słabe/domyślne klucze, minimum 16 znaków
6. **Input Validation** — Pydantic `Field(min_length, max_length)` na wszystkich schematach
7. **Docs Hidden** — `/docs` ukryty w produkcji (`app_debug=False`)
8. **HTTPS Enforce** — HSTS header + HTTP→HTTPS redirect w produkcji
9. **Server-Side Tier** — limit optymalizacji egzekwowany w backendzie (nie tylko frontend)
10. **API Key Server-Side** — frontend proxy wstrzykuje klucz, nie jest w client bundle
11. **SSRF Protection** — URL domain allowlist + private IP rejection na wszystkich user-supplied URLs
12. **Per-IP Tracking** — daily limit per IP, nie globalny

---

## Nowe pliki stworzone

| Plik | Cel |
|------|-----|
| `backend/utils/__init__.py` | Package init |
| `backend/utils/url_validator.py` | Shared URL validation — SSRF protection, marketplace domain allowlist, private IP rejection |

---

## Commity security

| Commit | Opis |
|--------|------|
| `deeab93` | Stripe hardening: URL bypass, backend verification, stripe_customer_id removal, rate limits, server-side tier |
| `66aeba3` | SSRF fixes, URL validation, batch tier limit, app_debug default, .gitignore |
| `36b4e86` | Hotfix: model_validator dla audit URL (Pydantic field order issue) |

---

## Testy na produkcji (2026-02-14)

| Test | Wynik |
|------|-------|
| SSRF: `http://169.254.169.254/latest/meta-data/` | "resolves to private/internal IP" |
| SSRF: `http://localhost:8000/health` | "Internal/private URLs are not allowed" |
| SSRF: `https://evil-site.com/steal` | "not a valid amazon domain" |
| `/docs` endpoint | 404 (ukryty) |
| `/api/stripe/status` response | Brak `stripe_customer_id` |
| Health check | `{"status":"healthy","database":"connected"}` |
