# Quick Start Guide - 5 Minutes to Running Backend

## Prerequisites
- Python 3.9+
- Supabase account (free)
- Groq API key (free)

## Step-by-Step Setup

### 1. Install Dependencies (1 min)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment (2 min)
```bash
# Copy template
cp .env.example .env

# Edit .env and add:
# - SUPABASE_URL (from supabase.com)
# - SUPABASE_KEY (anon key)
# - SUPABASE_SERVICE_KEY (service role key)
# - DATABASE_URL (from Supabase Settings → Database)
# - GROQ_API_KEY (from groq.com)
```

### 3. Setup Database (1 min)
```bash
# Go to Supabase SQL Editor
# Copy content from migrations/001_initial_schema.sql
# Paste and run
```

### 4. Verify Setup (30 sec)
```bash
python verify_setup.py
```

### 5. Start API (30 sec)
```bash
./start.sh
# or
uvicorn main:app --reload
```

## That's It!

✅ API running: http://localhost:8000
✅ Docs: http://localhost:8000/docs
✅ Health: http://localhost:8000/health

## First Test

```bash
# Import a product
curl -X POST http://localhost:8000/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "TEST-123",
    "title": "My First Product",
    "price": 99.99,
    "currency": "PLN",
    "images": [],
    "attributes": {}
  }'

# Optimize it
curl -X POST "http://localhost:8000/api/ai/optimize/1?target_marketplace=amazon"

# List products
curl http://localhost:8000/api/products
```

## Troubleshooting

**Database connection failed?**
- Check DATABASE_URL in .env
- Verify Supabase project is active
- Run migration SQL

**Groq API error?**
- Verify GROQ_API_KEY is correct
- Check groq.com for API status

**Import error?**
- Check all dependencies installed
- Activate venv: `source venv/bin/activate`

## Next Steps

1. ✅ Read API_EXAMPLES.md for more examples
2. ✅ Configure n8n webhook
3. ✅ Set up Redis for background jobs (optional)
4. ✅ Deploy to Railway/Render (see DEPLOYMENT.md)

## Common Commands

```bash
# Start API
./start.sh

# Verify setup
python verify_setup.py

# Run tests (when added)
pytest

# Start worker (optional)
dramatiq workers.ai_worker

# Check logs
# Railway: railway logs
# Render: Check dashboard
# Local: See terminal output
```

## API Cheat Sheet

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API docs |
| `/api/import/product` | POST | Import single product |
| `/api/ai/optimize/{id}` | POST | Optimize listing |
| `/api/export/publish/{id}` | POST | Publish to marketplace |
| `/api/products` | GET | List products |

## Getting Help

1. Check `/docs` for interactive API documentation
2. Read README.md for detailed guide
3. Check logs in terminal
4. Review code comments (lots of WHY explanations)

## What's Working

✅ Product import (webhook + API)
✅ AI optimization (Groq)
✅ Database storage (Supabase)
✅ Product listing/filtering
✅ Background jobs (structure ready)
✅ Health checks

## What Needs Configuration

⚙️ Marketplace API credentials (for actual publishing)
⚙️ Redis (for background jobs, optional)
⚙️ Custom domain (for production)

---

**Time to first API call: ~5 minutes**
**Time to first optimized listing: ~6 minutes**
**Time to production: ~30 minutes** (with deployment)
