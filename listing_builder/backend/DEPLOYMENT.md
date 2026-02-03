# Deployment Guide - Marketplace Listing Automation Backend

Guide for deploying to production (Railway, Render, or similar).

## Prerequisites

- Supabase account (for PostgreSQL)
- Groq API key (get from groq.com)
- Redis instance (Railway Redis or Redis Cloud)
- Git repository

## Option 1: Railway (Recommended)

Railway provides the simplest deployment with built-in Redis.

### 1. Setup Railway

```bash
# Install Railway CLI
npm install -g railway

# Login
railway login

# Initialize project
cd backend
railway init
```

### 2. Add Redis Service

In Railway dashboard:
1. Click "New"
2. Select "Redis"
3. Deploy Redis instance

### 3. Configure Environment Variables

In Railway dashboard → Variables:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (Railway auto-provides REDIS_URL)
REDIS_URL=${{Redis.REDIS_URL}}

# Groq AI
GROQ_API_KEY=gsk_your_groq_api_key

# App Config
APP_ENV=production
APP_DEBUG=False
API_SECRET_KEY=your-random-secret-key-change-this
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Webhook
WEBHOOK_SECRET=your-webhook-secret-token

# Marketplace APIs (optional initially)
AMAZON_REFRESH_TOKEN=
AMAZON_CLIENT_ID=
AMAZON_CLIENT_SECRET=
EBAY_APP_ID=
KAUFLAND_CLIENT_KEY=
```

### 4. Deploy

```bash
# Deploy from CLI
railway up

# Or connect GitHub repo in dashboard for auto-deploy
```

### 5. Run Database Migration

After first deploy:

1. Go to Supabase SQL Editor
2. Copy content from `migrations/001_initial_schema.sql`
3. Run the SQL

### 6. Verify Deployment

```bash
# Check health
curl https://your-app.railway.app/health

# Check docs
open https://your-app.railway.app/docs
```

## Option 2: Render

### 1. Create Web Service

1. Go to render.com
2. Click "New +" → "Web Service"
3. Connect your Git repo
4. Configure:
   - Name: `marketplace-backend`
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2. Add Redis

1. Click "New +" → "Redis"
2. Choose free plan
3. Get connection URL

### 3. Environment Variables

Add in Render dashboard:
- Same as Railway (see above)
- Use Render's Redis URL

### 4. Deploy

Render auto-deploys on git push.

## Option 3: Vercel (Functions)

Vercel can run FastAPI as serverless functions, but has limitations:
- No background workers (Dramatiq won't work)
- Use Vercel KV (Redis alternative)
- Limited execution time (10s on free tier)

**Not recommended for this project** due to background job requirements.

## Option 4: Docker + VPS

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: dramatiq workers.ai_worker
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - redis
      - api
```

Deploy to any VPS:

```bash
# Copy files
scp -r backend/ user@your-vps:~/

# SSH to VPS
ssh user@your-vps

# Deploy
cd backend
docker-compose up -d
```

## Background Workers

### Railway/Render

Add a second service for workers:

**Railway:**
```bash
# In Railway dashboard, add "New Service"
# Select same repo
# Override start command:
dramatiq workers.ai_worker
```

**Render:**
```bash
# Create "Background Worker"
# Start Command: dramatiq workers.ai_worker
```

### Docker

Workers included in docker-compose.yml above.

## Database Setup (Supabase)

### 1. Create Supabase Project

1. Go to supabase.com
2. Create new project
3. Wait for provisioning (~2 minutes)

### 2. Run Migration

1. Go to SQL Editor
2. Create new query
3. Paste content from `migrations/001_initial_schema.sql`
4. Run query

### 3. Get Connection Details

Settings → Database:
- Connection string → Direct connection
- Copy to `DATABASE_URL`

Settings → API:
- URL → Copy to `SUPABASE_URL`
- anon public → Copy to `SUPABASE_KEY`
- service_role → Copy to `SUPABASE_SERVICE_KEY`

## Redis Setup

### Railway

Built-in, just reference `${{Redis.REDIS_URL}}`.

### Render

Built-in, get URL from Redis instance.

### Redis Cloud (External)

1. Go to redis.com
2. Create free database
3. Get connection URL
4. Set as `REDIS_URL`

## Environment Variables Checklist

Before deploying, ensure these are set:

**Required:**
- [ ] `DATABASE_URL`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `REDIS_URL`
- [ ] `GROQ_API_KEY`
- [ ] `APP_ENV=production`
- [ ] `APP_DEBUG=False`
- [ ] `API_SECRET_KEY`
- [ ] `CORS_ORIGINS`
- [ ] `WEBHOOK_SECRET`

**Optional (can add later):**
- [ ] `AMAZON_REFRESH_TOKEN`
- [ ] `AMAZON_CLIENT_ID`
- [ ] `AMAZON_CLIENT_SECRET`
- [ ] `EBAY_APP_ID`
- [ ] `KAUFLAND_CLIENT_KEY`

## Post-Deployment

### 1. Verify Health

```bash
curl https://your-app-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### 2. Test Endpoints

```bash
# Get API info
curl https://your-app-url/

# Check docs
open https://your-app-url/docs
```

### 3. Test Import

```bash
curl -X POST https://your-app-url/api/import/product \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "PROD-001",
    "title": "Test Product",
    "price": 99.99,
    "currency": "PLN",
    "images": [],
    "attributes": {}
  }'
```

### 4. Configure n8n Webhook

In your n8n workflow:
1. Set webhook URL: `https://your-app-url/api/import/webhook`
2. Add header: `X-Webhook-Secret: your-webhook-secret`
3. Test the webhook

## Monitoring

### Railway

Built-in monitoring:
- Logs → View in dashboard
- Metrics → CPU, memory, network
- Deployments → History and rollback

### Render

Similar to Railway:
- Logs tab
- Metrics tab
- Auto-deploy on push

### External Monitoring (Optional)

**Sentry (Error Tracking):**
```bash
pip install sentry-sdk[fastapi]
```

In `main.py`:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**Uptime Monitoring:**
- UptimeRobot (free)
- Pingdom
- StatusCake

Monitor: `https://your-app-url/health`

## Scaling

### Railway/Render

Auto-scaling available on paid plans:
- Vertical: Increase memory/CPU
- Horizontal: Multiple instances

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
from locust import HttpUser, task

class ApiUser(HttpUser):
    @task
    def health_check(self):
        self.client.get("/health")

# Run test
locust -f locustfile.py --host=https://your-app-url
```

## Troubleshooting

### Database Connection Failed

- Check `DATABASE_URL` format
- Verify Supabase project is running
- Check firewall rules
- Try direct connection string

### Redis Connection Failed

- Verify `REDIS_URL` format
- Check Redis instance status
- Test connection: `redis-cli -u $REDIS_URL ping`

### Workers Not Running

- Check worker service logs
- Verify Redis connection
- Ensure worker service has same env vars

### Groq API Errors

- Verify `GROQ_API_KEY` is correct
- Check Groq dashboard for rate limits
- Try test request: `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"`

### CORS Errors

- Check `CORS_ORIGINS` includes your frontend URL
- Use exact protocol (https vs http)
- No trailing slashes in URLs

## Security Checklist

Before going live:

- [ ] Change `API_SECRET_KEY` to random string
- [ ] Change `WEBHOOK_SECRET` to random string
- [ ] Use HTTPS (Railway/Render auto-provide)
- [ ] Restrict CORS to specific domains
- [ ] Use Supabase service role key (not anon key) for backend
- [ ] Enable Supabase RLS if needed
- [ ] Don't expose `/docs` in production (optional)
- [ ] Set up rate limiting (TODO)
- [ ] Enable request logging
- [ ] Set up error monitoring

## Cost Estimates

### Free Tier Setup

- **Supabase**: Free (500MB DB, 50K monthly active users)
- **Railway**: $5/month credit (enough for hobby project)
- **Groq**: Free tier available
- **Redis**: Free on Railway/Render
- **Total**: ~$0-5/month

### Production Setup

- **Supabase Pro**: $25/month (8GB DB)
- **Railway/Render**: $20-50/month (scaled)
- **Groq**: Pay-as-you-go (~$0.10/1M tokens)
- **Redis**: Included
- **Total**: ~$50-100/month

## Next Steps

After successful deployment:

1. Configure marketplace APIs (Amazon, eBay, Kaufland)
2. Set up monitoring and alerts
3. Add API authentication
4. Implement rate limiting
5. Set up CI/CD pipeline
6. Add automated tests
7. Configure backup strategy

## Support

For deployment issues:
- Railway: discord.gg/railway
- Render: render.com/docs
- Supabase: supabase.com/docs
