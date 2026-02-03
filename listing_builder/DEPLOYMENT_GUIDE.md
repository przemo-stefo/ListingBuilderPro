# Production Deployment Guide
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23
**Target:** Railway (Backend) + Vercel (Frontend)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Backend Deployment (Railway)](#backend-deployment-railway)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Database Setup (Supabase)](#database-setup-supabase)
6. [Redis Configuration](#redis-configuration)
7. [Environment Variables](#environment-variables)
8. [Domain & SSL Setup](#domain--ssl-setup)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Post-Deployment Verification](#post-deployment-verification)
11. [Troubleshooting](#troubleshooting)
12. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

Before starting deployment, ensure you have:

### Required Accounts
- [ ] **GitHub account** (free) - for code repository
- [ ] **Railway account** (free tier) - for backend hosting
- [ ] **Vercel account** (free tier) - for frontend hosting
- [ ] **Supabase account** (free tier) - for PostgreSQL database
- [ ] **Groq account** (free tier) - for AI optimization

### Required Tools
- [ ] **Git** installed and configured
- [ ] **Node.js 18+** for local testing
- [ ] **Python 3.11+** for local testing
- [ ] **cURL** or **Postman** for API testing

### Required Knowledge
- Basic understanding of Git (push/pull/commit)
- Familiarity with environment variables
- Ability to follow step-by-step instructions
- NO DevOps experience required!

---

## Quick Start (5 Minutes)

**For experienced users who want to deploy ASAP:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/listing-builder.git
cd listing-builder

# 2. Backend to Railway
cd backend
railway init
railway up
# Add environment variables in Railway dashboard

# 3. Frontend to Vercel
cd ../frontend
vercel
# Follow prompts, add NEXT_PUBLIC_API_URL

# 4. Setup Supabase
# - Create project at supabase.com
# - Run migrations/001_initial_schema.sql
# - Copy connection details to Railway env vars

# Done! Visit your-app.vercel.app
```

For detailed step-by-step instructions, continue reading below.

---

## Backend Deployment (Railway)

Railway is the simplest way to deploy FastAPI backends with built-in Redis, PostgreSQL, and automatic HTTPS.

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign up with GitHub (recommended for automatic deployments)
4. Verify your email

**Cost:** Free tier includes $5/month credit (enough for hobby projects)

### Step 2: Install Railway CLI (Optional)

The CLI is optional but makes deployment easier.

```bash
# macOS
brew install railway

# Windows
npm install -g railway

# Linux
curl -fsSL https://railway.app/install.sh | sh
```

**Login:**
```bash
railway login
```

This opens your browser to authenticate.

### Step 3: Create New Railway Project

**Option A: Using Dashboard (Easier)**

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will detect it's a Python project
5. Click **"Add variables"** (we'll add them next)

**Option B: Using CLI**

```bash
cd backend
railway init
# Follow prompts to create new project
```

### Step 4: Add Redis Service

Redis is required for background job processing (Dramatiq workers).

1. In your Railway project dashboard
2. Click **"+ New"** → **"Database"** → **"Add Redis"**
3. Railway automatically provisions Redis
4. Connection URL is auto-injected as `${{Redis.REDIS_URL}}`

**Cost:** Free tier includes Redis

### Step 5: Configure Backend Environment Variables

In Railway dashboard → **Variables** tab, add these:

```bash
# Database (Supabase) - Get from Supabase dashboard
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR_PROJECT].supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (Railway auto-provides)
REDIS_URL=${{Redis.REDIS_URL}}

# Groq AI - Get from console.groq.com
GROQ_API_KEY=gsk_your_groq_api_key_here

# Application Settings
APP_ENV=production
APP_DEBUG=False
API_SECRET_KEY=generate-random-64-char-string-here
CORS_ORIGINS=https://your-frontend.vercel.app

# Webhook Security
WEBHOOK_SECRET=generate-random-32-char-string-here

# Marketplace APIs (add later when ready)
AMAZON_REFRESH_TOKEN=
AMAZON_CLIENT_ID=
AMAZON_CLIENT_SECRET=
EBAY_APP_ID=
KAUFLAND_CLIENT_KEY=
```

**How to generate secure random strings:**

```bash
# API_SECRET_KEY (64 characters)
openssl rand -hex 32

# WEBHOOK_SECRET (32 characters)
openssl rand -hex 16
```

### Step 6: Configure Build Settings

Railway should auto-detect Python, but verify:

1. Go to **Settings** tab
2. Check **Build Command:** `pip install -r requirements.txt`
3. Check **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Python Version:** 3.11 (or latest)

If not set, add these manually.

### Step 7: Deploy Backend

**Option A: Automatic Deployment (Recommended)**

Railway auto-deploys when you push to GitHub:

```bash
git add .
git commit -m "feat: Configure for Railway deployment"
git push origin main
```

Railway will:
- Detect the push
- Install dependencies
- Run migrations (if configured)
- Start the application
- Assign a public URL

**Option B: Manual Deployment (CLI)**

```bash
cd backend
railway up
```

### Step 8: Add Background Worker Service

The system needs a separate worker process for AI optimization jobs.

1. In Railway project, click **"+ New"** → **"Empty Service"**
2. Name it: `worker`
3. Connect to same GitHub repository
4. Override **Start Command:** `dramatiq workers.ai_worker`
5. Add same environment variables as backend (copy all)
6. Deploy

**Important:** Worker needs access to Redis and Database, so all env vars must match.

### Step 9: Get Backend URL

After deployment completes:

1. Go to **Settings** tab
2. Find **Public Domain** (e.g., `your-app.up.railway.app`)
3. Copy this URL - you'll need it for frontend configuration

**Test backend is running:**

```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

---

## Frontend Deployment (Vercel)

Vercel is the best hosting platform for Next.js applications, created by the Next.js team.

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"**
3. Sign up with GitHub (recommended)
4. Verify your email

**Cost:** Free tier includes unlimited personal projects

### Step 2: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

**Login:**
```bash
vercel login
```

### Step 3: Deploy Frontend

**Option A: Using Vercel Dashboard (Easier)**

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **"Import Git Repository"**
3. Select your repository
4. **Root Directory:** Set to `frontend`
5. **Framework Preset:** Next.js (auto-detected)
6. Click **"Add Environment Variable"**
7. Add: `NEXT_PUBLIC_API_URL` = `https://your-backend.up.railway.app`
8. Click **"Deploy"**

Vercel will:
- Install dependencies
- Build Next.js application
- Deploy to global CDN
- Assign a public URL (e.g., `your-app.vercel.app`)

**Option B: Using Vercel CLI**

```bash
cd frontend
vercel

# Follow prompts:
# - Setup and deploy? [Y]
# - Which scope? [Your account]
# - Link to existing project? [N]
# - What's your project's name? [marketplace-frontend]
# - In which directory is your code? [./]
# - Want to override settings? [N]
```

Add environment variable:
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Paste: https://your-backend.up.railway.app
```

Deploy to production:
```bash
vercel --prod
```

### Step 4: Configure Environment Variables

In Vercel dashboard → **Settings** → **Environment Variables**:

```bash
# Backend API URL (REQUIRED)
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

# Optional: Analytics
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=your-analytics-id
```

**Important:** Environment variable names starting with `NEXT_PUBLIC_` are exposed to the browser.

### Step 5: Update CORS on Backend

The backend needs to allow requests from your Vercel frontend.

1. Go to Railway dashboard
2. Open backend service
3. Edit `CORS_ORIGINS` environment variable:
   ```bash
   CORS_ORIGINS=https://your-app.vercel.app,https://your-app-staging.vercel.app
   ```
4. Save and redeploy

### Step 6: Test Frontend

Visit your Vercel URL (e.g., `https://your-app.vercel.app`)

**Check:**
- [ ] Dashboard loads
- [ ] Stats display (not all zeros)
- [ ] Navigation works
- [ ] Can view products page
- [ ] No CORS errors in browser console

**If you see CORS errors:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Verify backend `CORS_ORIGINS` includes your Vercel URL
- Check browser console for exact error

---

## Database Setup (Supabase)

Supabase provides managed PostgreSQL with a generous free tier.

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up with GitHub
3. Click **"New Project"**
4. Fill in:
   - **Name:** `marketplace-listings`
   - **Database Password:** Generate strong password (save it!)
   - **Region:** Choose closest to your users
   - **Pricing Plan:** Free
5. Click **"Create new project"**
6. Wait 2-3 minutes for provisioning

### Step 2: Run Database Migration

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Open `backend/migrations/001_initial_schema.sql` locally
4. Copy entire SQL content
5. Paste into Supabase SQL editor
6. Click **"Run"**

**Expected output:**
```
Success. No rows returned
```

This creates all necessary tables:
- `products`
- `bulk_jobs`
- Indexes for performance
- Triggers for timestamps

### Step 3: Get Connection Details

**For Backend Environment Variables:**

1. Go to **Settings** → **Database**
2. Find **Connection string** section
3. Choose **URI** (not session pooler)
4. Copy the connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

**For API Keys:**

1. Go to **Settings** → **API**
2. Copy:
   - **URL:** `https://[PROJECT].supabase.co`
   - **anon public:** `eyJhbGci...` (for frontend)
   - **service_role:** `eyJhbGci...` (for backend - keep secret!)

### Step 4: Add to Railway Environment Variables

Go to Railway → Backend → Variables and update:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

Click **"Save"** - Railway will redeploy automatically.

### Step 5: Verify Database Connection

Test that backend can connect:

```bash
curl https://your-backend.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

If `"database": "disconnected"`:
- Check `DATABASE_URL` format
- Verify password is correct
- Check Supabase project is active

### Step 6: Enable Row Level Security (Optional)

For additional security, enable RLS:

1. Go to **Authentication** → **Policies**
2. For `products` table, add policy:
   ```sql
   CREATE POLICY "Allow backend service access"
   ON products
   FOR ALL
   TO service_role
   USING (true)
   WITH CHECK (true);
   ```

This ensures only your backend (with service_role key) can modify data.

---

## Redis Configuration

Redis is used for background job processing and caching.

### Railway Redis (Recommended)

Railway provides managed Redis - already configured in Step 4 of Backend Deployment.

**Verify Redis is working:**

```bash
# SSH into Railway container (if needed)
railway run redis-cli -u $REDIS_URL ping
```

Expected output: `PONG`

### Alternative: Redis Cloud (External)

If you need more Redis features or capacity:

1. Go to [redis.com](https://redis.com)
2. Create free database (30MB)
3. Get connection URL: `redis://default:password@endpoint:port`
4. Add to Railway environment variables:
   ```bash
   REDIS_URL=redis://default:password@redis-12345.cloud.redis.com:12345
   ```

**Cost:** Free tier: 30MB, $5/month for 250MB

---

## Environment Variables

Complete reference for all environment variables.

### Backend Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql://postgres:pass@host:5432/db` |
| `SUPABASE_URL` | ✅ Yes | Supabase project URL | `https://abc.supabase.co` |
| `SUPABASE_KEY` | ✅ Yes | Supabase anon public key | `eyJhbGci...` |
| `SUPABASE_SERVICE_KEY` | ✅ Yes | Supabase service role key | `eyJhbGci...` |
| `REDIS_URL` | ✅ Yes | Redis connection URL | `redis://user:pass@host:6379/0` |
| `GROQ_API_KEY` | ✅ Yes | Groq API key for AI | `gsk_xxx` |
| `APP_ENV` | ✅ Yes | Environment name | `production` |
| `APP_DEBUG` | ✅ Yes | Debug mode (off in prod) | `False` |
| `API_SECRET_KEY` | ✅ Yes | Secret key for JWT/sessions | Random 64 chars |
| `CORS_ORIGINS` | ✅ Yes | Allowed frontend URLs | `https://app.vercel.app` |
| `WEBHOOK_SECRET` | ✅ Yes | Webhook authentication | Random 32 chars |
| `AMAZON_REFRESH_TOKEN` | ❌ No | Amazon SP-API token | (optional) |
| `AMAZON_CLIENT_ID` | ❌ No | Amazon SP-API client ID | (optional) |
| `AMAZON_CLIENT_SECRET` | ❌ No | Amazon SP-API secret | (optional) |
| `EBAY_APP_ID` | ❌ No | eBay Developer App ID | (optional) |
| `KAUFLAND_CLIENT_KEY` | ❌ No | Kaufland API key | (optional) |

### Frontend Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API URL | `https://api.railway.app` |
| `NEXT_PUBLIC_VERCEL_ANALYTICS_ID` | ❌ No | Vercel Analytics ID | (optional) |

### Environment Variable Checklist

Before deploying, verify all required variables are set:

**Backend:**
```bash
railway run env | grep -E "DATABASE_URL|SUPABASE_URL|REDIS_URL|GROQ_API_KEY|API_SECRET_KEY|CORS_ORIGINS"
```

All should return values (not empty).

**Frontend:**
```bash
vercel env ls
```

Should show `NEXT_PUBLIC_API_URL` set for production.

---

## Domain & SSL Setup

### Custom Domain for Backend (Railway)

1. Go to Railway project → Backend service
2. Click **Settings** → **Domains**
3. Click **"Generate Domain"** (free Railway subdomain)
   - You get: `your-app-production.up.railway.app`
   - HTTPS is automatic

**Or add custom domain:**

4. Click **"Custom Domain"**
5. Enter: `api.yourdomain.com`
6. Railway provides DNS records to add:
   ```
   Type: CNAME
   Name: api
   Value: your-app.up.railway.app
   ```
7. Add these records in your domain registrar (Namecheap, GoDaddy, etc.)
8. Wait 5-10 minutes for DNS propagation
9. Railway automatically provisions SSL certificate (free, via Let's Encrypt)

**Cost:** $0 (Railway subdomains and SSL are free)

### Custom Domain for Frontend (Vercel)

1. Go to Vercel project → **Settings** → **Domains**
2. Click **"Add"**
3. Enter: `app.yourdomain.com`
4. Vercel provides DNS records:
   ```
   Type: CNAME
   Name: app
   Value: cname.vercel-dns.com
   ```
5. Add records in your domain registrar
6. Wait 5-10 minutes for propagation
7. Vercel automatically provisions SSL certificate

**Cost:** $0 (Vercel SSL is free)

### Update CORS After Adding Custom Domain

After adding custom domains, update backend CORS:

```bash
CORS_ORIGINS=https://app.yourdomain.com,https://your-app.vercel.app
```

Include both custom domain and Vercel subdomain for flexibility.

---

## CI/CD Pipeline

Automate testing and deployment with GitHub Actions.

### Setup GitHub Repository

1. Push code to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/listing-builder.git
   git push -u origin main
   ```

2. Both Railway and Vercel will auto-detect and deploy on push

### Configure Automatic Deployments

**Railway:**
1. Go to Railway project → **Settings**
2. Under **Source**, verify GitHub repo is connected
3. Enable **"Auto-deploy on push"**
4. Choose branch: `main`

**Vercel:**
1. Go to Vercel project → **Settings** → **Git**
2. Verify repository is connected
3. **Production Branch:** `main`
4. **Preview Branches:** All other branches (for testing)

### GitHub Actions Workflows

See `.github/workflows/` for automated tests and deployments (created in Task 8).

**Workflow on every push:**
1. Run backend tests (pytest)
2. Run frontend type checking (tsc)
3. Build frontend (next build)
4. Deploy to Railway (if main branch)
5. Deploy to Vercel (if main branch)

---

## Post-Deployment Verification

After deployment, verify everything works.

### Backend Health Check

```bash
curl https://your-backend.up.railway.app/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

✅ **Pass:** All checks pass
❌ **Fail:** Check [Troubleshooting](#troubleshooting)

### Frontend Load Test

Open browser to: `https://your-app.vercel.app`

**Check:**
- [ ] Dashboard loads (no blank page)
- [ ] Stats display real data (not all zeros)
- [ ] Navigation works (click Products, Import, etc.)
- [ ] No JavaScript errors in console (F12 → Console)
- [ ] Images load correctly
- [ ] Page is responsive on mobile (resize browser)

### End-to-End Test

Test the complete workflow:

1. **Import a product:**
   ```bash
   curl -X POST https://your-backend.up.railway.app/api/import/product \
     -H "Content-Type: application/json" \
     -d '{
       "source_id": "test001",
       "title": "Production Test Product",
       "description": "Testing deployment",
       "price": 99.99,
       "currency": "USD",
       "images": ["https://via.placeholder.com/300"],
       "category": "Test"
     }'
   ```

2. **View product in UI:**
   - Go to `https://your-app.vercel.app/products`
   - Find "Production Test Product" in list
   - Click "View Details"

3. **Optimize product:**
   - In product details, click "Optimize for Amazon"
   - Wait 5-10 seconds
   - Verify optimized title and description appear

4. **Check worker is processing:**
   - Go to Railway → Worker service → Logs
   - Should see: `Optimizing product ID: 1`

✅ **Pass:** Complete workflow works
❌ **Fail:** See specific troubleshooting section below

### API Documentation

Verify API docs are accessible:

```bash
open https://your-backend.up.railway.app/docs
```

This opens interactive Swagger UI where you can:
- View all endpoints
- Test API calls directly
- See request/response schemas

**Security Note:** Consider disabling `/docs` in production by setting:
```bash
APP_DISABLE_DOCS=True
```

### Performance Verification

Test response times:

```bash
# Backend health (should be <100ms)
time curl https://your-backend.up.railway.app/health

# Frontend load (should be <2s)
time curl https://your-app.vercel.app

# List products (should be <500ms for 20 products)
time curl https://your-backend.up.railway.app/api/products?page_size=20
```

If slower:
- Check database indexes (see OPTIMIZATION_GUIDE.md)
- Verify Redis is connected (caching helps)
- Check Railway/Vercel region matches user location

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Backend Returns 502 Bad Gateway

**Symptoms:**
- Frontend shows "Failed to fetch"
- cURL to backend returns 502

**Causes & Fixes:**

**A. Application crashed on startup**
```bash
# Check Railway logs
railway logs

# Look for errors:
# - ModuleNotFoundError → missing dependency in requirements.txt
# - Database connection failed → check DATABASE_URL
# - Redis connection failed → check REDIS_URL
```

**Fix:** Add missing dependency or fix environment variable

**B. Port binding issue**
```bash
# Backend must bind to 0.0.0.0:$PORT (Railway injects PORT)
# Check start command is:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**C. Health check failing**
```bash
# Railway health checks /health endpoint
# If it fails 3 times, Railway stops the service
# Check logs for health check errors
```

**Fix:** Ensure `/health` endpoint is working

#### 2. Database Connection Failed

**Symptoms:**
- Health check returns `"database": "disconnected"`
- Logs show: `could not connect to server`

**Fixes:**

**A. Wrong DATABASE_URL format**
```bash
# Correct format:
postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Common mistakes:
# - Missing password
# - Wrong port (should be 5432)
# - Wrong database name (should be postgres)
```

**B. Password contains special characters**
```bash
# URL-encode the password
# Example: pass@word → pass%40word
# Use online URL encoder
```

**C. Supabase paused project**
```bash
# Free tier projects pause after 1 week of inactivity
# Go to Supabase dashboard → Click "Resume project"
```

**D. IP whitelist issue**
```bash
# Supabase allows all IPs by default
# Check: Settings → Database → Connection Pooling
# Ensure "Restrict access" is OFF for Railway
```

#### 3. CORS Errors in Browser

**Symptoms:**
- Browser console shows: `Access-Control-Allow-Origin` error
- Frontend can't fetch data from backend

**Fixes:**

**A. CORS_ORIGINS not set correctly**
```bash
# In Railway → Variables, check:
CORS_ORIGINS=https://your-app.vercel.app

# Must match EXACTLY (no trailing slash)
# Must include protocol (https://)
# Multiple domains: comma-separated
CORS_ORIGINS=https://app1.vercel.app,https://app2.vercel.app
```

**B. Wrong API URL in frontend**
```bash
# In Vercel → Environment Variables, check:
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

# Must include protocol (https://)
# NO trailing slash
# Redeploy frontend after changing
```

**C. Railway domain changed**
```bash
# If you regenerate Railway domain, update:
# 1. Vercel → NEXT_PUBLIC_API_URL
# 2. Railway → CORS_ORIGINS (might have changed)
```

#### 4. Groq API Errors

**Symptoms:**
- Optimization fails with 401 Unauthorized
- Logs show: `Invalid API key`

**Fixes:**

**A. Invalid Groq API key**
```bash
# Get new key from console.groq.com
# Copy and paste carefully (no extra spaces)
# Update Railway → Variables → GROQ_API_KEY
```

**B. Groq rate limit hit**
```bash
# Free tier limits:
# - 30 requests/minute
# - 14,400 requests/day

# Check Groq dashboard for usage
# Wait or upgrade to paid plan
```

**C. Groq service outage**
```bash
# Check https://status.groq.com
# If down, wait and retry
# Consider adding fallback to OpenAI (see OPTIMIZATION_GUIDE.md)
```

#### 5. Worker Not Processing Jobs

**Symptoms:**
- Optimization stuck on "Processing..."
- Worker logs empty or show errors

**Fixes:**

**A. Worker service not deployed**
```bash
# Check Railway dashboard → Worker service exists
# If not, add it (see Step 8 of Backend Deployment)
```

**B. Worker missing environment variables**
```bash
# Worker needs ALL same env vars as backend:
# - DATABASE_URL
# - REDIS_URL
# - GROQ_API_KEY
# - SUPABASE_* keys
# Copy all from backend to worker
```

**C. Redis connection failed**
```bash
# Check worker logs for "Redis connection failed"
# Verify REDIS_URL is correct
# Test: railway run redis-cli -u $REDIS_URL ping
```

**D. Dramatiq broker issue**
```bash
# Check backend logs for:
# "Failed to enqueue job to Dramatiq"

# Fix: Restart Redis service in Railway
# Or: Check Redis service is running
```

#### 6. Frontend Not Loading

**Symptoms:**
- Blank page
- "This page isn't working"
- Console errors

**Fixes:**

**A. Build failed**
```bash
# Check Vercel deployment logs
# Look for:
# - TypeScript errors → fix type issues
# - Module not found → install missing package
# - Build out of memory → upgrade Vercel plan
```

**B. Environment variables not set**
```bash
# Vercel → Settings → Environment Variables
# Must have: NEXT_PUBLIC_API_URL
# Must be set for "Production" environment
# Redeploy after adding
```

**C. CSP (Content Security Policy) blocking API**
```bash
# Check browser console for CSP errors
# Add to next.config.js:
headers: async () => [{
  source: '/(.*)',
  headers: [
    { key: 'Content-Security-Policy', value: "connect-src 'self' https://your-backend.up.railway.app" }
  ]
}]
```

#### 7. Slow Performance

**Symptoms:**
- Pages load slowly (>3 seconds)
- API calls timeout
- Optimization takes >30 seconds

**Fixes:**

**A. Database not indexed**
```bash
# Check indexes exist:
psql $DATABASE_URL -c "\d products"

# Should show indexes on:
# - id (primary key)
# - status
# - source_marketplace
# - created_at

# If missing, run migration again
```

**B. N+1 query problem**
```bash
# Check backend logs for multiple queries per request
# Fix: Use SQLAlchemy eager loading
# See OPTIMIZATION_GUIDE.md for details
```

**C. No caching enabled**
```bash
# Verify Redis is working:
railway run redis-cli -u $REDIS_URL ping

# Check backend uses Redis for caching
# See OPTIMIZATION_GUIDE.md for caching strategies
```

**D. Too many concurrent optimizations**
```bash
# Groq rate limit: 30 requests/minute
# Batch optimize max 5 products at a time
# Add queue management (see OPTIMIZATION_GUIDE.md)
```

---

## Rollback Procedures

If something breaks after deployment, quickly rollback.

### Railway Rollback

**Option 1: Redeploy Previous Version (Fastest)**

1. Go to Railway project → Backend service
2. Click **"Deployments"** tab
3. Find last working deployment
4. Click **"..."** menu → **"Redeploy"**
5. Confirm

Takes ~2 minutes to rollback.

**Option 2: Revert Git Commit**

```bash
# Find commit to revert
git log --oneline

# Revert to previous commit
git revert HEAD

# Push
git push origin main
```

Railway auto-deploys the reverted version.

### Vercel Rollback

**Option 1: Instant Rollback (Easiest)**

1. Go to Vercel project → **"Deployments"**
2. Find last working deployment
3. Click **"..."** → **"Promote to Production"**
4. Confirm

Rollback is instant (global CDN updates in seconds).

**Option 2: Revert Git Commit**

Same as Railway - Vercel auto-deploys on push.

### Database Rollback

**⚠️ DANGER:** Database rollbacks are tricky. Prevention is better than cure.

**Option 1: Restore from Supabase Backup**

1. Go to Supabase → **Database** → **Backups**
2. Choose backup point (daily automatic backups)
3. Click **"Restore"**
4. Confirm (this WILL overwrite current data!)

**Option 2: Manual SQL Rollback**

If you have SQL migration down script:

```bash
# Connect to database
psql $DATABASE_URL

# Run down migration
\i migrations/001_down.sql
```

**Prevention:**
- Test migrations on staging first
- Always have down migrations
- Take manual backup before schema changes:
  ```bash
  pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
  ```

### Emergency Maintenance Mode

If you need to take the site down temporarily:

**Backend:**
```bash
# In Railway → Variables, add:
MAINTENANCE_MODE=true

# Backend will return 503 Service Unavailable
```

**Frontend:**
```bash
# Create maintenance.html page:
# Vercel → Settings → Redirects → Add:
# Source: /*
# Destination: /maintenance.html
# Permanent: No
```

Users see maintenance page instead of broken site.

---

## Next Steps

After successful deployment:

1. ✅ **Configure Monitoring** - See [MONITORING_GUIDE.md](./MONITORING_GUIDE.md)
2. ✅ **Optimize Performance** - See [OPTIMIZATION_GUIDE.md](./OPTIMIZATION_GUIDE.md)
3. ✅ **Setup Backups** - See [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md)
4. ✅ **Plan for Scale** - See [SCALING_GUIDE.md](./SCALING_GUIDE.md)
5. ✅ **Configure Marketplace APIs** - Add Amazon/eBay/Kaufland credentials
6. ✅ **Setup Domain** - Add custom domain for professional branding
7. ✅ **Enable Analytics** - Add Vercel Analytics and Railway monitoring
8. ✅ **Create Backups** - Schedule automatic database backups

---

## Support & Resources

**Official Documentation:**
- Railway: [docs.railway.app](https://docs.railway.app)
- Vercel: [vercel.com/docs](https://vercel.com/docs)
- Supabase: [supabase.com/docs](https://supabase.com/docs)
- Groq: [console.groq.com/docs](https://console.groq.com/docs)

**Community Support:**
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Vercel Discord: [vercel.com/discord](https://vercel.com/discord)
- Supabase Discord: [discord.supabase.com](https://discord.supabase.com)

**Status Pages:**
- Railway: [status.railway.app](https://status.railway.app)
- Vercel: [vercel-status.com](https://vercel-status.com)
- Supabase: [status.supabase.com](https://status.supabase.com)
- Groq: [status.groq.com](https://status.groq.com)

**Deployment Issues:**
- Check logs first (Railway/Vercel dashboards)
- Verify all environment variables
- Test locally before deploying
- Ask in Discord communities

---

**Congratulations! Your Marketplace Listing Automation System is now live in production!** 🎉
