# listing_builder/CLAUDE.md
# Purpose: Project-specific instructions for Claude Code
# NOT for: Global Claude settings (that's ~/.claude/CLAUDE.md)

## Architecture

- **Frontend:** Next.js 14 + TypeScript + Tailwind (Vercel)
- **Backend:** FastAPI + Groq LLM + Supabase PostgreSQL (grzegorz152 Docker, Cloudflare Tunnel)
- **Proxy:** Frontend `/api/proxy/[...path]` → injects `X-API-Key` server-side → backend
- **Auth:** JWT (Supabase ES256 JWKS + HS256 fallback) → `middleware/supabase_auth.py`, API key fallback → `middleware/auth.py`
- **LLM:** Groq `llama-3.3-70b-versatile` (default), 6 API keys for rotation on 429

## URLs

| What | URL |
|------|-----|
| Frontend (prod) | https://panel.octohelper.com |
| Backend (prod) | https://api-lbp.feedmasters.org |
| Frontend (alt) | https://listing-builder-pro.vercel.app |
| Backend (Render) | SUSPENDED + auto-deploy OFF — nie używać |
| Health check | `GET /health` |

## Deploy

```bash
# Frontend (Vercel) — MANUAL
cd listing_builder/frontend && npx vercel --prod

# Backend (grzegorz152) — Docker + Cloudflare Tunnel
cd listing_builder/deploy/grzegorz152 && bash deploy.sh

# Render — SUSPENDED + auto-deploy OFF (2026-02-23)
# To resume: Render Dashboard → Resume Service → Enable auto-deploy
```

## Key Patterns

### Proxy Allowlist (CRITICAL)
New backend paths MUST be added to `frontend/src/app/api/proxy/[...path]/route.ts` `ALLOWED_PATH_PREFIXES`.

### PUBLIC_PATHS (no API key required)
`/health`, `/`, `/docs`, `/openapi.json`, `/api/stripe/webhook`, `/api/import/webhook`, OAuth callbacks.
Everything else requires `X-API-Key` header via middleware.

### SSRF Protection
`utils/url_validator.py` — `validate_marketplace_url()` checks marketplace domain allowlist + rejects private IPs.

### SQLAlchemy + PostgreSQL
NEVER use `:param::jsonb` — SQLAlchemy misparses it. Use `CAST(:param AS jsonb)` instead.

### Models
All UUID columns: `PG_UUID(as_uuid=False)` — NOT `String(36)`.

### Render (SUSPENDED)
Service `srv-d644kr0gjchc739fjdq0` — suspended + auto-deploy OFF since 2026-02-23.
If resuming: `PUT /v1/services/{id}/env-vars` replaces ALL vars (never POST). Verify count after PUT.

### Supabase Migrations
Use Management API: `POST https://api.supabase.com/v1/projects/{ref}/database/query`
with `Authorization: Bearer {mgmt_token}`. NOT RPC.

## Monetization

- **Monthly only:** 49 PLN/mies via Stripe Checkout (subscription mode)
- License key system — `premium_licenses` table
- Free tier: 3 optimizations/day (per-IP), Amazon only
- Premium: unlimited optimizations, all marketplaces, full features

## File Conventions

- File headers: `# path/to/file.py` + `# Purpose:` + `# NOT for:`
- Comments explain WHY, not WHAT
- Files under 200 lines (ideally <150)
- Dark mode: `#1A1A1A`, `#121212`, neutral grays — NEVER purple/violet

<!-- secretless:managed -->
## Secretless Mode

This project uses Secretless to protect credentials from AI context.

**Available API keys** (set as env vars — use `$VAR_NAME` in commands, never ask for values):

| Env Var | Service | Auth Header |
|---------|---------|-------------|
| `$ANTHROPIC_API_KEY` | Anthropic Messages API | `x-api-key: $ANTHROPIC_API_KEY` |

**Blocked file patterns** (never read, write, or reference):
- `.env`, `.env.*` — environment variable files
- `*.key`, `*.pem`, `*.p12`, `*.pfx` — private key files
- `.aws/credentials`, `.ssh/*` — cloud/SSH credentials
- `*.tfstate`, `*.tfvars` — Terraform state with secrets
- `secrets/`, `credentials/` — secret directories

**If you need a credential:**
1. Reference it via `$VAR_NAME` in shell commands or `process.env.VAR_NAME` in code
2. Never hardcode credentials in source files
3. Never print or echo key values — only reference them as variables

Verify setup: `npx secretless-ai verify`

## Transcript Protection
- NEVER ask users to paste API keys, tokens, or passwords into the conversation
- Credentials in this conversation are automatically redacted by Secretless AI
