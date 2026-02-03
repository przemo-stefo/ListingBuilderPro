# Production Launch Checklist
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23

---

## Pre-Launch Checklist

Complete this checklist before going live. Each item must be ✅ before launch.

---

## 1. Infrastructure Setup

### Backend (Railway)
- [ ] Backend deployed to Railway
- [ ] Worker service deployed separately
- [ ] Custom domain configured (optional)
- [ ] HTTPS enabled (automatic on Railway)
- [ ] Health check endpoint working (`/health` returns 200)

### Frontend (Vercel)
- [ ] Frontend deployed to Vercel
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic on Vercel)
- [ ] No JavaScript errors in browser console
- [ ] All pages load correctly

### Database (Supabase)
- [ ] Production database created
- [ ] Initial migration run successfully
- [ ] Database indexes created (see OPTIMIZATION_GUIDE.md)
- [ ] Row Level Security configured (optional)
- [ ] Backup schedule enabled (automatic on Pro plan)

### Redis
- [ ] Redis instance running on Railway
- [ ] Connection tested from backend
- [ ] Cache working (check logs for cache hits)

---

## 2. Environment Variables

### Backend Environment Variables (Railway)
- [ ] `DATABASE_URL` - Supabase connection string
- [ ] `SUPABASE_URL` - Supabase project URL
- [ ] `SUPABASE_KEY` - Anon public key
- [ ] `SUPABASE_SERVICE_KEY` - Service role key (keep secret!)
- [ ] `REDIS_URL` - Redis connection string
- [ ] `GROQ_API_KEY` - Groq API key for AI
- [ ] `APP_ENV=production` - Environment name
- [ ] `APP_DEBUG=False` - Debug mode OFF
- [ ] `API_SECRET_KEY` - Random 64-char string (generated)
- [ ] `CORS_ORIGINS` - Frontend URL (exact match)
- [ ] `WEBHOOK_SECRET` - Random 32-char string (generated)

### Frontend Environment Variables (Vercel)
- [ ] `NEXT_PUBLIC_API_URL` - Backend API URL (with https://)

### Verification
```bash
# Backend
railway run env | grep -E "DATABASE_URL|GROQ_API_KEY|CORS_ORIGINS"

# Frontend
vercel env ls
```

---

## 3. Security Hardening

### Secrets & Keys
- [ ] All secrets are random, not defaults
- [ ] `API_SECRET_KEY` is 64+ characters
- [ ] `WEBHOOK_SECRET` is 32+ characters
- [ ] No hardcoded credentials in code
- [ ] `.env` files in `.gitignore`
- [ ] Supabase `service_role` key used in backend (not `anon`)

### CORS Configuration
- [ ] `CORS_ORIGINS` includes only your frontend domain
- [ ] No wildcards (`*`) in CORS
- [ ] Protocol matches exactly (https:// not http://)
- [ ] No trailing slashes in URLs

### API Protection
- [ ] Rate limiting enabled (see OPTIMIZATION_GUIDE.md)
- [ ] Webhook endpoint requires secret header
- [ ] SQL injection prevented (using Pydantic validators)
- [ ] XSS prevention (React escapes by default)

### Database Security
- [ ] Row Level Security enabled (optional, Supabase)
- [ ] Service role key not exposed to frontend
- [ ] Database password is strong (20+ characters)
- [ ] Database accessible only from Railway IPs (optional)

---

## 4. Performance Optimization

### Backend
- [ ] Database indexes created (`002_add_indexes.sql`)
- [ ] Connection pooling configured
- [ ] Gzip compression enabled
- [ ] Redis caching implemented for dashboard stats
- [ ] Async route handlers used

### Frontend
- [ ] Code splitting enabled (Next.js default)
- [ ] Images optimized (Next.js Image component)
- [ ] TanStack Query configured for caching
- [ ] Lazy loading for heavy components
- [ ] Bundle size <1MB (check Vercel build output)

### Database
```sql
-- Verify indexes exist
\d products

-- Should show:
-- idx_products_status
-- idx_products_created_at
-- idx_products_source
```

---

## 5. Monitoring Setup

### Health Checks
- [ ] UptimeRobot configured (or Better Uptime)
- [ ] Monitoring backend `/health` endpoint
- [ ] Email alerts on downtime
- [ ] Check interval: 5 minutes

### Error Tracking
- [ ] Sentry configured on backend
- [ ] Sentry configured on frontend
- [ ] Test error tracking (trigger test error)
- [ ] Alert rules configured (>10 errors in 5 min)

### Analytics
- [ ] Vercel Analytics enabled
- [ ] Core Web Vitals tracking
- [ ] Business metrics dashboard

### Logging
- [ ] Structured logging enabled (structlog)
- [ ] Log level set to INFO (not DEBUG) in production
- [ ] Logs accessible in Railway dashboard
- [ ] Critical errors logged

---

## 6. Testing

### Backend API Tests
```bash
# Health check
curl https://your-api.railway.app/health
# Expected: {"status": "healthy", "database": "connected"}

# Import product
curl -X POST https://your-api.railway.app/api/import/product \
  -H "Content-Type: application/json" \
  -d '{"source_id": "test001", "title": "Test", "price": 99.99, "currency": "USD"}'
# Expected: {"status": "success", "product_id": 1}

# List products
curl https://your-api.railway.app/api/products
# Expected: {"items": [...], "total": 1}

# Optimize product
curl -X POST "https://your-api.railway.app/api/ai/optimize/1?target_marketplace=amazon"
# Expected: Optimized product with title/description
```

### Frontend Tests
- [ ] Dashboard loads and shows stats
- [ ] Products page shows imported products
- [ ] Product detail page works
- [ ] Import form works (try adding a product)
- [ ] Optimization works (try optimizing a product)
- [ ] No console errors (F12 → Console)

### End-to-End Test
- [ ] Import product via API
- [ ] View product in frontend
- [ ] Optimize product via UI
- [ ] Check optimized result
- [ ] Delete product
- [ ] Verify deleted

### Load Testing (Optional)
```bash
# Install Apache Bench
# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 https://your-api.railway.app/health

# Expected: 95% of requests < 500ms
```

---

## 7. Backup & Recovery

### Database Backups
- [ ] Supabase automatic backups enabled (Pro plan)
- [ ] Manual backup taken before launch:
  ```bash
  pg_dump $DATABASE_URL > backup_pre_launch.sql
  ```
- [ ] Backup stored securely (not in repo)
- [ ] Restore procedure tested

### Rollback Plan
- [ ] Previous working deployment ID noted
- [ ] Rollback procedure documented (see DEPLOYMENT_GUIDE.md)
- [ ] Team knows how to rollback quickly

---

## 8. Documentation

### Internal Documentation
- [ ] README.md up to date
- [ ] API documentation accessible (`/docs`)
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Troubleshooting guide available

### Team Training
- [ ] Team knows how to access logs
- [ ] Team knows how to rollback
- [ ] Team knows monitoring dashboard
- [ ] On-call rotation defined (if applicable)

---

## 9. Cost Management

### Budget
- [ ] Monthly budget defined (e.g., $100/month)
- [ ] Spending alerts configured (Railway, Vercel, Supabase)
- [ ] Cost tracking spreadsheet created

### Limits
- [ ] Railway spending limit set
- [ ] Supabase auto-pause disabled (Pro plan)
- [ ] Groq rate limits understood
- [ ] Bandwidth limits monitored

---

## 10. Final Checks

### 24 Hours Before Launch
- [ ] All tests passing
- [ ] No critical bugs in Sentry
- [ ] Performance metrics acceptable (p95 <500ms)
- [ ] Team briefed on launch plan
- [ ] Support email/chat ready

### Launch Day
- [ ] Deploy backend first
- [ ] Verify health check
- [ ] Deploy frontend
- [ ] Verify frontend connects to backend
- [ ] Run smoke tests
- [ ] Monitor for 1 hour
- [ ] Announce launch

### First Week After Launch
- [ ] Check logs daily
- [ ] Monitor error rate (should be <1%)
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Address any issues quickly

---

## Sign-Off

**Pre-Launch Review:**
- [ ] All checklist items completed
- [ ] No blocking issues
- [ ] Team ready
- [ ] Monitoring in place

**Approved by:**
- [ ] Technical Lead: _______________  Date: _______
- [ ] Product Owner: _______________  Date: _______

---

## Emergency Contacts

**If something breaks:**

1. **Check health status:**
   - UptimeRobot: uptimerobot.com
   - Railway status: status.railway.app
   - Vercel status: vercel-status.com
   - Supabase status: status.supabase.com

2. **View logs:**
   - Railway: `railway logs --service backend`
   - Vercel: Vercel dashboard → Deployments → Logs

3. **Rollback if needed:**
   - See DEPLOYMENT_GUIDE.md → Rollback Procedures

4. **Get help:**
   - Railway Discord: discord.gg/railway
   - Vercel Discord: vercel.com/discord
   - Supabase Discord: discord.supabase.com

---

## Post-Launch Tasks

**First 30 Days:**
- [ ] Monitor daily (5 min/day)
- [ ] Review weekly metrics
- [ ] Address user feedback
- [ ] Optimize based on real usage
- [ ] Update documentation as needed

**See also:**
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment procedures
- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - Monitoring setup
- [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) - Backup & recovery

---

**You're ready to launch! 🚀**
