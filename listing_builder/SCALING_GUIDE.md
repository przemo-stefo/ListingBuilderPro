# Scaling Guide
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23

---

## Growth Stages

| Stage | Users/Day | Products/Month | Monthly Cost | Infrastructure |
|-------|-----------|----------------|--------------|----------------|
| **MVP** | <100 | <1,000 | $0-10 | Free tiers |
| **Startup** | 100-1,000 | 1K-10K | $65-100 | Railway+Vercel+Supabase |
| **Growth** | 1K-10K | 10K-100K | $150-300 | 2-3 instances + read replicas |
| **Scale** | 10K-100K | 100K-1M | $500-1,000 | Auto-scaling, multi-region |
| **Enterprise** | >100K | >1M | $1,000+ | Dedicated infrastructure |

---

## Vertical Scaling (Increase Resources)

### When to Scale Vertically

**Indicators:**
- CPU consistently >80%
- Memory >85%
- API response time >500ms (p95)
- Database connections maxed out

### Railway Scaling

**Current:** 1 instance, 1GB RAM, 1 CPU

**Upgrade Steps:**
1. Go to Railway → Service → Settings
2. **Plan:** Change from Hobby ($20) to Pro ($20+)
3. **Resources:** Increase RAM to 2GB ($10 more)
4. **CPU:** Add 1 more vCPU ($10 more)

**Cost:** $40/month (vs $20)
**Capacity:** 2-3x more throughput

### Database Scaling (Supabase)

**Free → Pro:** $25/month
- 8GB database (vs 500MB)
- 50GB bandwidth (vs 2GB)
- No pausing
- Point-in-time recovery
- Daily backups

**Pro → Team:** $599/month
- 100GB database
- Read replicas
- SOC2 compliance

---

## Horizontal Scaling (Add More Servers)

### When to Scale Horizontally

- Vertical scaling maxed out
- Need redundancy/high availability
- Want zero-downtime deployments

### Multi-Instance Backend

**Railway Configuration:**
1. Go to Service → Settings
2. **Replicas:** Change from 1 to 3
3. Railway auto-balances load

**Benefits:**
- 3x capacity
- One instance can fail, others continue
- Rolling updates (zero downtime)

**Cost:** 3 × $20 = $60/month

### Load Balancing

Railway provides automatic load balancing across replicas.

**How it works:**
```
User Request
     ↓
Railway Load Balancer
     ↓
┌────────┬────────┬────────┐
│ API #1 │ API #2 │ API #3 │
└────────┴────────┴────────┘
     ↓
  Database
```

### Worker Scaling

**Separate worker instances for background jobs:**

1. Create new service: "Worker"
2. Same code as backend
3. Start command: `dramatiq workers.ai_worker --processes 4`
4. Scale workers independently

**Benefits:**
- API responds fast (jobs offloaded)
- Scale workers separately from API
- Can have 1 API + 5 workers for heavy processing

---

## Database Scaling

### Read Replicas

**When:** Database CPU >70%, mostly reads

**Setup (Supabase Pro):**
1. Enable read replica in dashboard
2. Use replica for reads:
   ```python
   # Writes → Primary
   db_write = create_engine(DATABASE_URL)
   
   # Reads → Replica
   db_read = create_engine(DATABASE_READ_REPLICA_URL)
   
   # Usage
   products = db_read.query(Product).all()  # Fast
   ```

**Cost:** +$25/month per replica
**Benefit:** 2x read capacity

### Connection Pooling

**PgBouncer (built into Supabase):**
- Handles 10,000 connections with only 100 DB connections
- Enable in Supabase → Database → Connection Pooler

**Use pooler URL:**
```
postgresql://postgres:pass@[project].pooler.supabase.com:6543/postgres
```

### Database Indexing

**Critical for scaling:**
```sql
-- Essential indexes
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_created_at ON products(created_at DESC);
CREATE INDEX idx_products_source ON products(source_marketplace);
```

See OPTIMIZATION_GUIDE.md for full indexing strategy.

---

## Redis/Caching Strategy

### Cache More Aggressively

```python
# Cache frequently accessed data for longer
redis_client.setex("stats:dashboard", 600, data)  # 10 minutes

# Cache product lists
redis_client.setex("products:list:page1", 300, data)  # 5 minutes

# Cache user sessions
redis_client.setex(f"session:{user_id}", 3600, data)  # 1 hour
```

### Redis Cluster (High Scale)

**When:** Redis CPU >80% or memory >4GB

**Options:**
1. **Redis Cloud Pro:** $60/month, 5GB, clustering
2. **AWS ElastiCache:** Fully managed Redis cluster
3. **Self-hosted Redis Cluster:** 3+ nodes

---

## CDN for Static Assets

### Vercel Edge Network (Included)

Automatically caches:
- Static pages
- Images (via Next.js Image)
- CSS/JS bundles

**Check cache headers:**
```bash
curl -I https://your-app.vercel.app/_next/static/...
# Look for: x-vercel-cache: HIT
```

### Cloudflare CDN (Optional)

For API responses caching:

1. Sign up at cloudflare.com (free)
2. Add your domain
3. Enable caching for API responses:
   ```
   Cache-Control: public, max-age=300
   ```

**Cost:** Free for basic CDN

---

## Auto-Scaling Strategy

### Railway Auto-Scaling

**Pro plan feature:**
- Set min/max replicas (1-10)
- Auto-scale based on CPU/Memory
- Scale up when >70% utilization
- Scale down when <30% utilization

**Configuration:**
```yaml
# railway.json
{
  "services": {
    "backend": {
      "autoscaling": {
        "enabled": true,
        "min": 2,
        "max": 10,
        "targetCPU": 70,
        "targetMemory": 80
      }
    }
  }
}
```

### Worker Auto-Scaling

**Scale workers based on queue length:**

```python
# Monitor queue
queue_length = redis_client.llen("dramatiq:default")

# If queue >100, scale up
if queue_length > 100:
    # Add more worker instances
    railway.scale_service("worker", replicas=5)

# If queue <10, scale down
elif queue_length < 10:
    railway.scale_service("worker", replicas=1)
```

---

## Breaking Points Analysis

### Current Limits (Free Tier)

| Resource | Limit | Bottleneck At |
|----------|-------|---------------|
| Database | 500MB | ~50K products |
| API Requests | Unlimited | CPU at ~1K concurrent |
| Groq API | 14,400/day | ~600 optimizations/hour |
| Bandwidth | 2GB/month | ~20K page views |

### Expected Growth

| Metric | Now | 3 Months | 6 Months | 12 Months |
|--------|-----|----------|----------|-----------|
| Users/day | 10 | 100 | 500 | 2,000 |
| Products | 100 | 5,000 | 25,000 | 100,000 |
| Optimizations/day | 50 | 500 | 2,000 | 10,000 |
| Cost/month | $0 | $65 | $150 | $300 |

---

## Cost-Effective Scaling

### Priority 1 (Free/Cheap Wins)

1. ✅ **Database indexes** - 10x faster, $0
2. ✅ **Redis caching** - Included in Railway
3. ✅ **Code splitting** - Faster frontend, $0
4. ✅ **Query optimization** - 5x faster, $0

### Priority 2 (Small Cost, Big Impact)

1. 💰 **Supabase Pro** - $25/mo, 16x more database
2. 💰 **2 backend instances** - $40/mo, 2x capacity
3. 💰 **Dedicated workers** - $20/mo, offload heavy jobs

### Priority 3 (High Scale Only)

1. 💰💰 **Read replicas** - $50/mo, needed at >10K users/day
2. 💰💰 **Auto-scaling** - $100+/mo, needed at >50K users/day
3. 💰💰 **Multi-region** - $200+/mo, global users

---

## Capacity Planning

### Current Capacity (Free Tier)

- **API:** ~1,000 requests/minute
- **Database:** ~50 queries/second
- **Optimizations:** ~10/minute (Groq limit)
- **Concurrent users:** ~50

### After Optimization (Same Cost)

- **API:** ~5,000 requests/minute (indexing + caching)
- **Database:** ~200 queries/second (connection pooling)
- **Optimizations:** ~10/minute (same Groq limit)
- **Concurrent users:** ~200

### Growth Plan ($150/month)

- **API:** ~20,000 requests/minute (3 instances)
- **Database:** ~500 queries/second (Pro + indexes)
- **Optimizations:** ~30/minute (Groq paid plan)
- **Concurrent users:** ~1,000

---

## Monitoring for Scale

### Key Metrics to Watch

**Before scaling:**
- CPU: <70%
- Memory: <80%
- API p95: <500ms
- Database connections: <80% of limit
- Error rate: <1%

**Time to scale:**
- CPU: >80% for 10+ minutes
- Memory: >90%
- API p95: >1000ms
- Database connections: >90%
- Error rate: >5%

---

## Scaling Checklist

### Before Scaling
- [ ] Optimize code (see OPTIMIZATION_GUIDE.md)
- [ ] Add database indexes
- [ ] Enable Redis caching
- [ ] Monitor for 1 week to confirm need

### Scaling Steps
- [ ] Document current metrics (baseline)
- [ ] Increase resources (vertical or horizontal)
- [ ] Monitor for 24 hours
- [ ] Load test new capacity
- [ ] Update monitoring alerts

### After Scaling
- [ ] Verify performance improvement
- [ ] Check costs are within budget
- [ ] Update documentation
- [ ] Plan next scaling trigger

---

## Real-World Scaling Examples

### 100 → 1,000 Users/Day

**Problem:** API slow, database maxed out
**Solution:**
1. Added database indexes ($0)
2. Enabled Redis caching ($0 - included)
3. Upgraded to Supabase Pro ($25/mo)
4. Added 1 more backend instance ($20/mo)

**Result:** 5x capacity for $45/mo

### 1,000 → 10,000 Users/Day

**Problem:** Workers can't keep up
**Solution:**
1. Separated workers from API ($20/mo)
2. Scaled workers to 3 instances ($40/mo extra)
3. Added read replica ($25/mo)
4. Optimized queries (saved $10/mo in resources)

**Result:** 10x capacity for $85/mo extra

---

## Next Steps

1. ✅ Monitor current usage for 1 week
2. ✅ Identify bottlenecks (see MONITORING_GUIDE.md)
3. ✅ Optimize before scaling (see OPTIMIZATION_GUIDE.md)
4. ✅ Scale when metrics consistently exceed 80%
5. ✅ Re-evaluate monthly based on growth

**See also:**
- [OPTIMIZATION_GUIDE.md](./OPTIMIZATION_GUIDE.md) - Free performance wins
- [COST_ANALYSIS.md](./COST_ANALYSIS.md) - Detailed cost breakdown
