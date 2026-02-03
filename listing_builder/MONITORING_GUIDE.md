# Production Monitoring Guide
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23

---

## Quick Start

**Essential monitoring (5 minutes setup):**

1. **Railway Monitoring** (built-in, free)
   - Logs: Railway Dashboard → Your Service → Logs
   - Metrics: CPU, Memory, Network usage
   - Deployments: Track deploy history

2. **Vercel Analytics** (built-in, free)
   - Go to Vercel → Your Project → Analytics
   - Enable Web Analytics (free)
   - Track: Page views, Core Web Vitals, user sessions

3. **Supabase Dashboard** (built-in, free)
   - Database size and connections
   - API requests and bandwidth
   - Slow query log

4. **Health Check Monitoring**
   ```bash
   # Use UptimeRobot (free, 50 monitors)
   # 1. Go to uptimerobot.com
   # 2. Add monitor: https://your-api.railway.app/health
   # 3. Check interval: 5 minutes
   # 4. Get email alerts on downtime
   ```

---

## Table of Contents

1. [Monitoring Stack](#monitoring-stack)
2. [Application Monitoring](#application-monitoring)
3. [Infrastructure Monitoring](#infrastructure-monitoring)
4. [Error Tracking](#error-tracking)
5. [Performance Monitoring](#performance-monitoring)
6. [Business Metrics](#business-metrics)
7. [Alerting Strategy](#alerting-strategy)
8. [Log Management](#log-management)
9. [Dashboards](#dashboards)
10. [Cost Monitoring](#cost-monitoring)

---

## Monitoring Stack

### Free Tier Setup (Recommended for Startups)

| Component | Service | Cost | Purpose |
|-----------|---------|------|---------|
| **Health Checks** | UptimeRobot | Free | Uptime monitoring |
| **Error Tracking** | Sentry | Free | Exception tracking |
| **Logs** | Railway/Vercel | Free | Application logs |
| **Metrics** | Railway Dashboard | Free | CPU/Memory/Network |
| **Analytics** | Vercel Analytics | Free | User behavior |
| **Database** | Supabase Dashboard | Free | DB performance |

**Total cost:** $0/month

### Professional Setup ($20/month)

| Component | Service | Cost | Purpose |
|-----------|---------|------|---------|
| Health Checks | Better Uptime | $10/mo | Advanced uptime |
| Error Tracking | Sentry Pro | $26/mo | Team features |
| APM | Railway | Free | App performance |
| Logs | Logtail | $0-10/mo | Log aggregation |
| Status Page | Statuspage.io | $29/mo | Public status |

---

## Application Monitoring

### 1. Health Check Endpoint

**Already implemented:** `GET /health`

```bash
curl https://your-api.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "groq_api": "available",
  "environment": "production",
  "uptime": 86400,
  "timestamp": "2026-01-23T10:00:00Z"
}
```

### 2. Setup UptimeRobot (Free)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Sign up (free)
3. Click **"+ Add New Monitor"**
4. Configure:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** "Backend API Health"
   - **URL:** `https://your-api.railway.app/health`
   - **Monitoring Interval:** 5 minutes (free tier)
   - **Alert Contacts:** Your email
5. Click **"Create Monitor"**

**Expected response:** `200 OK` with "healthy" in body

**Alerts:** Email notification if:
- Site is down (>5 minutes)
- Response time >2 seconds
- HTTP status code ≠ 200

### 3. Setup Better Uptime (Paid, $10/month)

For advanced monitoring:

1. Go to [betteruptime.com](https://betteruptime.com)
2. Sign up for Pro plan ($10/month)
3. Features:
   - **1-minute checks** (vs 5 minutes on free)
   - **Status page** (public.yourdomain.com)
   - **Incident management**
   - **On-call scheduling**
   - **SMS alerts** (included)

---

## Infrastructure Monitoring

### 1. Railway Monitoring

Built-in monitoring in Railway dashboard:

**CPU Usage:**
- Go to Service → Metrics → CPU
- Target: <70% average
- Alert if: >90% for 5+ minutes

**Memory Usage:**
- Go to Service → Metrics → Memory
- Target: <80% of allocated
- Alert if: >95% (risk of OOM)

**Network:**
- Inbound/Outbound traffic
- Monitor for unusual spikes

**Custom Alerts:**
```bash
# Railway CLI to check metrics
railway metrics --service backend --metric cpu

# Output:
# Average CPU: 45%
# Peak CPU: 78%
# Current: 52%
```

### 2. Vercel Monitoring

**Real-time Analytics:**
- Go to Vercel → Project → Analytics
- View:
  - **Page views**
  - **Unique visitors**
  - **Top pages**
  - **Referrers**
  - **Devices** (mobile vs desktop)

**Core Web Vitals:**
- **LCP** (Largest Contentful Paint): <2.5s = good
- **FID** (First Input Delay): <100ms = good
- **CLS** (Cumulative Layout Shift): <0.1 = good

Alert if metrics exceed thresholds.

### 3. Database Monitoring (Supabase)

**Dashboard Metrics:**
1. Go to Supabase → Project → Database
2. Monitor:
   - **Database size:** 500MB limit on free tier
   - **Active connections:** Max 100 on free tier
   - **API requests:** Track usage patterns
   - **Bandwidth:** 2GB/month on free tier

**Slow Query Log:**
1. Go to SQL Editor
2. Run:
   ```sql
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   WHERE mean_time > 100  -- Queries >100ms
   ORDER BY total_time DESC
   LIMIT 20;
   ```

**Connection Pool Monitoring:**
```sql
SELECT count(*) AS connections,
       state
FROM pg_stat_activity
GROUP BY state;
```

Expected:
- Active: 5-20
- Idle: 10-50
- Idle in transaction: 0 (problem if >0)

---

## Error Tracking

### 1. Setup Sentry (Recommended)

**Backend Integration:**

```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]
```

**File:** `backend/main.py`

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1,  # Sample 10% of transactions
    profiles_sample_rate=0.1,
)

app = FastAPI()
```

**Frontend Integration:**

```bash
npm install @sentry/nextjs
```

**File:** `frontend/sentry.client.config.js`

```javascript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://your-sentry-dsn@sentry.io/project-id",
  environment: "production",
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

**Get Sentry DSN:**
1. Sign up at [sentry.io](https://sentry.io) (free tier: 5k errors/month)
2. Create project → Select FastAPI (backend) and Next.js (frontend)
3. Copy DSN
4. Add to Railway environment variables:
   ```bash
   SENTRY_DSN=https://xxx@sentry.io/xxx
   ```

**What Sentry Tracks:**
- ✅ Unhandled exceptions
- ✅ API errors (4xx, 5xx)
- ✅ Performance issues
- ✅ Slow database queries
- ✅ User context (IP, browser, etc.)

### 2. Error Alerting

**Configure in Sentry Dashboard:**
1. Go to Settings → Alerts
2. Create alert:
   - **Condition:** Error count >10 in 5 minutes
   - **Action:** Email notification
   - **Priority:** High

---

## Performance Monitoring

### 1. API Response Time

**Backend Metrics (Structured Logging):**

**File:** `backend/middleware/performance.py`

```python
import time
import structlog
from fastapi import Request

logger = structlog.get_logger()

@app.middleware("http")
async def log_performance(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "api_request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )

    # Alert if slow
    if duration > 1.0:  # >1 second
        logger.warning(
            "slow_api_request",
            path=request.url.path,
            duration_ms=round(duration * 1000, 2)
        )

    return response
```

**View Logs:**
```bash
railway logs --service backend | grep "slow_api_request"
```

### 2. Database Query Performance

**Log Slow Queries:**

```python
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Log queries >100ms
@event.listens_for(Engine, "before_cursor_execute")
def log_slow_queries(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 0.1:  # >100ms
        logger.warning(
            "slow_database_query",
            duration_ms=round(total * 1000, 2),
            query=statement[:200]  # First 200 chars
        )
```

---

## Business Metrics

### Track Key Metrics

**File:** `backend/api/metrics_routes.py`

```python
from fastapi import APIRouter
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/metrics/dashboard")
async def get_dashboard_metrics():
    """Business metrics for monitoring"""

    # Product metrics
    total_products = db.query(Product).count()
    products_today = db.query(Product).filter(
        Product.created_at >= datetime.now() - timedelta(days=1)
    ).count()

    # Optimization metrics
    optimizations_today = db.query(Product).filter(
        Product.status == "optimized",
        Product.updated_at >= datetime.now() - timedelta(days=1)
    ).count()

    # Publishing metrics
    published_today = db.query(Product).filter(
        Product.status == "published",
        Product.published_at >= datetime.now() - timedelta(days=1)
    ).count()

    # Error rate
    failed_today = db.query(Product).filter(
        Product.status == "failed",
        Product.updated_at >= datetime.now() - timedelta(days=1)
    ).count()

    return {
        "total_products": total_products,
        "products_today": products_today,
        "optimizations_today": optimizations_today,
        "published_today": published_today,
        "failed_today": failed_today,
        "error_rate": failed_today / max(products_today, 1)
    }
```

**Create Dashboard in Grafana/Metabase:**
- Track daily imports
- Optimization success rate
- Publishing success rate
- API response times

---

## Alerting Strategy

### Critical Alerts (Immediate Action Required)

| Alert | Condition | Action | Channel |
|-------|-----------|--------|---------|
| **API Down** | Health check fails 3x | Investigate immediately | SMS + Email |
| **Database Down** | Connection fails | Check Supabase status | SMS + Email |
| **High Error Rate** | >5% errors in 5 min | Check logs, rollback if needed | Email + Slack |
| **Out of Memory** | Memory >95% | Restart service, upgrade plan | Email |
| **Disk Full** | Database >90% of limit | Clean up or upgrade | Email |

### Warning Alerts (Monitor, Non-Critical)

| Alert | Condition | Action | Channel |
|-------|-----------|--------|---------|
| **Slow API** | p95 >500ms | Check optimization guide | Email |
| **High CPU** | >80% for 10 min | Monitor, consider scaling | Email |
| **Rate Limit Hit** | Groq API rate limit | Implement queueing | Email |
| **Low Cache Hit** | Redis hit rate <80% | Review caching strategy | Email |

### Informational (Daily Digest)

| Metric | Frequency | Channel |
|--------|-----------|---------|
| Daily summary | Once per day | Email |
| Weekly report | Monday 9am | Email |
| Monthly costs | 1st of month | Email |

---

## Log Management

### Structured Logging

**Already implemented:** `structlog` in backend

**View Logs:**

**Railway:**
```bash
# Real-time logs
railway logs --service backend --tail

# Search logs
railway logs --service backend | grep "ERROR"

# Export logs
railway logs --service backend --since 1h > logs.txt
```

**Vercel:**
```bash
# Real-time logs
vercel logs your-deployment-url --follow

# Search by status code
vercel logs your-deployment-url --status 500
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Development only | Detailed variable values |
| **INFO** | Normal operation | Request completed, job started |
| **WARNING** | Unusual but handled | Slow query, rate limit approached |
| **ERROR** | Recoverable error | API call failed, will retry |
| **CRITICAL** | System failure | Database down, cannot continue |

**Set Log Level:**
```bash
# Railway → Environment Variables
LOG_LEVEL=INFO  # Production
LOG_LEVEL=DEBUG  # Staging
```

---

## Dashboards

### 1. Railway Dashboard

**Default metrics (no setup needed):**
- CPU usage over time
- Memory usage over time
- Network in/out
- Request count
- Deployment history

**Access:** Railway Dashboard → Your Service → Metrics

### 2. Custom Dashboard (Optional)

**Using Grafana + Prometheus (free, self-hosted):**

See `monitoring/docker-compose.monitoring.yml` for setup.

**Metrics to track:**
- API response time (p50, p95, p99)
- Database connection pool utilization
- Redis cache hit rate
- Worker queue length
- Error rate by endpoint

---

## Cost Monitoring

### Track Monthly Costs

| Service | Free Tier Limit | Overage Cost | Monitor |
|---------|----------------|--------------|---------|
| **Railway** | $5 credit | $0.000231/GB-hour | Usage in dashboard |
| **Vercel** | 100GB bandwidth | $40/100GB | Analytics → Usage |
| **Supabase** | 500MB DB, 2GB bandwidth | $25/month Pro | Database → Usage |
| **Groq** | 14,400 req/day | Pay-as-you-go | console.groq.com |

### Cost Alerts

**Railway:**
1. Go to Settings → Billing
2. Set spending limit: $50/month
3. Get email at 50%, 80%, 100%

**Supabase:**
1. Go to Settings → Billing
2. Pausing: Auto-pause after 1 week inactivity (free tier)
3. Alerts: Email at 80% of bandwidth

### Cost Optimization

**Daily review:**
```bash
# Check Railway usage
railway status

# Check Vercel bandwidth
vercel project ls --stats

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('postgres'));"
```

---

## Monitoring Checklist

### Daily (5 minutes)
- [ ] Check health check status (UptimeRobot)
- [ ] Review error count (Sentry)
- [ ] Check deployment status (Railway/Vercel)
- [ ] Monitor CPU/Memory usage (Railway dashboard)

### Weekly (30 minutes)
- [ ] Review performance metrics (API response times)
- [ ] Check database slow queries (Supabase)
- [ ] Review cost usage (Railway/Vercel/Supabase)
- [ ] Check cache hit rate (Redis)
- [ ] Review business metrics (products imported/optimized/published)

### Monthly (2 hours)
- [ ] Analyze trends (traffic, errors, performance)
- [ ] Review and adjust alerts
- [ ] Plan capacity upgrades if needed
- [ ] Review and optimize costs
- [ ] Update documentation

---

## Quick Troubleshooting

**High error rate:**
1. Check Sentry → See which endpoint is failing
2. Check Railway logs → Find error details
3. Rollback if critical (see DEPLOYMENT_GUIDE.md)

**Slow API:**
1. Check slow query log in Supabase
2. Review optimization guide (OPTIMIZATION_GUIDE.md)
3. Check if Redis is caching properly

**High costs:**
1. Review bandwidth usage (Vercel Analytics)
2. Check database size (Supabase dashboard)
3. Reduce retention if needed

---

## Next Steps

1. ✅ Setup UptimeRobot for health checks (5 min)
2. ✅ Integrate Sentry for error tracking (15 min)
3. ✅ Enable Vercel Analytics (1 min)
4. ✅ Create alert rules (10 min)
5. ✅ Review logs daily for 1 week
6. ✅ Set up custom dashboard (optional, 1 hour)

**See also:**
- [OPTIMIZATION_GUIDE.md](./OPTIMIZATION_GUIDE.md) - Improve performance
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Rollback procedures
