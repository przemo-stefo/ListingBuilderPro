# Disaster Recovery & Backup Strategy
# Marketplace Listing Automation System

**Version:** 1.0.0
**Last Updated:** 2026-01-23

---

## Quick Recovery Guide

**If something breaks:**

1. **Check status pages** (2 minutes)
   - Railway: status.railway.app
   - Vercel: vercel-status.com
   - Supabase: status.supabase.com

2. **Rollback deployment** (5 minutes)
   - Railway: Dashboard → Deployments → Redeploy previous
   - Vercel: Dashboard → Deployments → Promote to Production

3. **Restore database** (10 minutes)
   - Supabase: Dashboard → Database → Backups → Restore

**RTO (Recovery Time Objective):** 15 minutes
**RPO (Recovery Point Objective):** 24 hours (daily backups)

---

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Recovery Procedures](#recovery-procedures)
3. [Disaster Scenarios](#disaster-scenarios)
4. [Business Continuity](#business-continuity)
5. [Testing & Drills](#testing--drills)

---

## Backup Strategy

### 1. Database Backups (Supabase)

**Automatic Backups (Pro Plan):**
- **Frequency:** Daily automatic backups
- **Retention:** 7 days (Pro), 30 days (Team)
- **Type:** Full database dump
- **Location:** Supabase managed storage
- **Cost:** Included in Pro plan ($25/month)

**Access backups:**
1. Go to Supabase Dashboard
2. Navigate to Database → Backups
3. See list of available backup points
4. Click "Restore" to restore database

**Manual Backup (Before Critical Changes):**

```bash
# Create manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress for storage
gzip backup_*.sql

# Upload to S3/Google Drive/Dropbox (optional)
aws s3 cp backup_*.sql.gz s3://your-backup-bucket/
```

**Schedule:** Manual backups before:
- Schema migrations
- Bulk data operations
- Major deployments
- Maintenance windows

### 2. Code Backups (GitHub)

**Already handled by Git:**
- Every commit is a backup point
- GitHub stores full history
- Can restore any previous version

**Additional protection:**
```bash
# Clone repository as backup
git clone --mirror https://github.com/yourusername/repo.git

# Store on external drive or another Git host (GitLab, Bitbucket)
```

### 3. Configuration Backups

**Environment Variables:**

```bash
# Backup Railway environment variables
railway variables > railway_env_backup_$(date +%Y%m%d).txt

# Backup Vercel environment variables
vercel env pull .env.production.backup

# Store securely (encrypted)
gpg --encrypt railway_env_backup_*.txt
```

**Frequency:** After any configuration change

### 4. Application Data Backups

**Export critical data regularly:**

```bash
# Export all products
curl https://your-api.railway.app/api/products/export > products_backup.json

# Export bulk jobs
curl https://your-api.railway.app/api/jobs/export > jobs_backup.json

# Schedule weekly
```

Add to cron (or GitHub Actions):
```bash
0 2 * * 0 /path/to/backup_script.sh  # Every Sunday 2am
```

---

## Recovery Procedures

### Scenario 1: Accidental Code Deployment (Buggy Release)

**Problem:** New code deployed with critical bug.

**Recovery (5 minutes):**

**Railway:**
1. Go to Railway Dashboard → Backend service
2. Click **Deployments** tab
3. Find last working deployment (green checkmark)
4. Click **"..."** → **"Redeploy"**
5. Wait 2-3 minutes for redeployment

**Vercel:**
1. Go to Vercel Dashboard → Project → Deployments
2. Find last working deployment
3. Click **"..."** → **"Promote to Production"**
4. Deployment is instant (global CDN updates in seconds)

**Verification:**
```bash
# Test health check
curl https://your-api.railway.app/health

# Test frontend
curl https://your-app.vercel.app
```

### Scenario 2: Database Corruption or Data Loss

**Problem:** Database data corrupted or accidentally deleted.

**Recovery (10-30 minutes):**

**Option 1: Restore from Supabase Backup**

1. Go to Supabase → Database → Backups
2. Choose restore point (e.g., yesterday's backup)
3. Click **"Restore"**
4. Confirm (WARNING: This will overwrite current database!)
5. Wait 5-10 minutes for restore
6. Verify data is restored:
   ```sql
   SELECT COUNT(*) FROM products;
   ```

**Option 2: Restore from Manual Backup**

```bash
# Download backup file
# Restore to Supabase
psql $DATABASE_URL < backup_YYYYMMDD.sql

# Or restore specific table
psql $DATABASE_URL << EOF
DROP TABLE products;
\i backup_products_only.sql
EOF
```

**Post-Recovery:**
- Check data integrity
- Notify users if data loss occurred
- Investigate root cause
- Prevent future occurrences

### Scenario 3: Complete Service Outage (Railway Down)

**Problem:** Railway has major outage, backend inaccessible.

**Temporary Recovery (Emergency):**

**Option 1: Deploy to Vercel Functions**

```bash
# Deploy backend as Vercel serverless functions (limited)
cd backend
vercel

# Note: Dramatiq workers won't work, but API will
```

**Option 2: Deploy to Render**

```bash
# Quick deploy to Render
render-cli deploy --from-git https://github.com/yourusername/repo
```

**Option 3: Run locally and expose with Ngrok**

```bash
# Start backend locally
cd backend
python main.py

# Expose publicly
ngrok http 8000

# Update Vercel NEXT_PUBLIC_API_URL temporarily
```

### Scenario 4: Database Service Down (Supabase Outage)

**Problem:** Supabase has outage, database unavailable.

**Short-term Mitigation:**
- Show maintenance page to users
- Cache existing data in Redis (if available)
- Queue writes for later processing

**Long-term Recovery:**
- Wait for Supabase to restore (check status.supabase.com)
- If extended outage, migrate to alternative:
  ```bash
  # Quick migration to Railway Postgres
  railway add postgres
  pg_dump $SUPABASE_URL | psql $RAILWAY_POSTGRES_URL
  ```

### Scenario 5: Accidentally Deleted Production Environment

**Problem:** Entire Railway project or Vercel project deleted.

**Recovery (30-60 minutes):**

**Redeploy from scratch:**

1. **Database:**
   ```bash
   # Create new Supabase project
   # Restore from backup
   psql $NEW_DATABASE_URL < latest_backup.sql
   ```

2. **Backend:**
   ```bash
   # Create new Railway project
   railway init
   railway add redis
   # Set all environment variables
   railway up
   ```

3. **Frontend:**
   ```bash
   # Create new Vercel project
   vercel
   # Set NEXT_PUBLIC_API_URL
   vercel env add NEXT_PUBLIC_API_URL production
   vercel --prod
   ```

4. **Update DNS** (if using custom domain)

**Total time:** 30-60 minutes (if you have backups!)

---

## Disaster Scenarios

### Critical Disasters (RTO: 15 minutes)

| Disaster | Impact | Recovery | Prevention |
|----------|--------|----------|------------|
| **Buggy deployment** | API returns errors | Rollback | Staging environment, testing |
| **Database crash** | Complete outage | Restore backup | Daily backups, monitoring |
| **DDoS attack** | Site unreachable | Cloudflare protection | Rate limiting, WAF |
| **API key leak** | Unauthorized access | Rotate keys immediately | Secrets management |

### Major Disasters (RTO: 1-4 hours)

| Disaster | Impact | Recovery | Prevention |
|----------|--------|----------|------------|
| **Railway outage** | Backend down | Deploy to Render/Vercel | Multi-cloud strategy |
| **Supabase outage** | Data unavailable | Wait or migrate | Database replicas |
| **Groq API down** | AI features down | Fallback to OpenAI | Multiple AI providers |
| **GitHub down** | Can't deploy | Deploy from local | Local Git mirrors |

### Catastrophic Disasters (RTO: 4-24 hours)

| Disaster | Impact | Recovery | Prevention |
|----------|--------|----------|------------|
| **All cloud providers down** | Complete system failure | Rebuild from backups | Offline backups, documentation |
| **Ransomware attack** | Data encrypted | Restore from offline backups | Security hardening, monitoring |
| **Account compromised** | Malicious changes | Contact support, restore | 2FA, IP whitelisting |

---

## Business Continuity

### Communication Plan

**If disaster occurs:**

1. **Internal notification** (immediate):
   - Alert team via Slack/Discord
   - Status: "Investigating issue"

2. **User notification** (within 15 minutes):
   - Update status page (if available)
   - Email notification to users
   - Social media post

3. **Regular updates** (every 30 minutes):
   - Progress on recovery
   - Estimated resolution time
   - Workarounds if available

**Template messages:**

**Initial:**
> "We're currently experiencing technical difficulties. Our team is investigating. Status updates: [status-page-url]"

**Update:**
> "Issue identified: [brief description]. ETA for resolution: [time]. Affected features: [list]"

**Resolved:**
> "Issue resolved. All systems operational. Root cause: [explanation]. Prevention: [steps taken]"

### Maintenance Windows

**Planned Maintenance:**
- Schedule during low-traffic hours (e.g., Sunday 2-4am)
- Notify users 48 hours in advance
- Take manual backup before maintenance
- Have rollback plan ready

### Data Retention Policy

| Data Type | Retention | Backup Frequency | Storage |
|-----------|-----------|------------------|---------|
| **Products** | Indefinite | Daily | Database |
| **Logs** | 30 days | Real-time | Railway/Vercel |
| **Metrics** | 90 days | Real-time | Monitoring tools |
| **Backups** | 30 days | Daily | Supabase + S3 |
| **User data** | Per GDPR | Daily | Database |

---

## Testing & Drills

### Monthly Backup Testing

**Test that backups actually work:**

```bash
# 1. Download latest backup
pg_dump $DATABASE_URL > test_backup.sql

# 2. Restore to test database
psql $TEST_DATABASE_URL < test_backup.sql

# 3. Verify data
psql $TEST_DATABASE_URL << EOF
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM bulk_jobs;
EOF

# 4. Document results
```

### Quarterly Disaster Recovery Drill

**Simulate complete outage:**

1. **Scenario:** Railway is down, need to deploy to alternative
2. **Action:** Deploy to Render from local backup
3. **Verification:** Confirm API is working
4. **Time:** Measure how long it takes
5. **Learnings:** Document gaps, improve procedures

### Annual Full Recovery Test

**Simulate catastrophic failure:**

1. Create fresh accounts on all services
2. Deploy entire system from backups only
3. Verify all functionality works
4. Measure total recovery time
5. Update documentation based on learnings

---

## Recovery Checklist

### Immediate Response (0-15 minutes)

- [ ] Identify issue (logs, monitoring)
- [ ] Notify team
- [ ] Post initial status update
- [ ] Stop any ongoing operations
- [ ] Preserve evidence (logs, screenshots)

### Short-term Recovery (15-60 minutes)

- [ ] Execute recovery procedure
- [ ] Verify recovery successful
- [ ] Post recovery status update
- [ ] Monitor for stability

### Post-Incident (1-24 hours)

- [ ] Conduct post-mortem
- [ ] Document root cause
- [ ] Implement preventive measures
- [ ] Update runbooks
- [ ] Notify users of resolution

### Follow-up (1-7 days)

- [ ] Review and improve monitoring
- [ ] Add tests to prevent recurrence
- [ ] Update disaster recovery plan
- [ ] Train team on new procedures

---

## Backup & Recovery Tools

### Essential Tools to Have Ready

```bash
# Install Railway CLI
brew install railway

# Install Vercel CLI
npm install -g vercel

# Install PostgreSQL client
brew install postgresql

# Install Redis client
brew install redis

# Install backup utility
pip install pgbackrest
```

### Emergency Contact List

**Service Status Pages:**
- Railway: https://status.railway.app
- Vercel: https://vercel-status.com
- Supabase: https://status.supabase.com
- Groq: https://status.groq.com

**Support Channels:**
- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- Supabase Discord: https://discord.supabase.com

---

## Cost of Disasters

### Estimated Impact

| Disaster | Downtime | Revenue Loss | Recovery Cost | Total Cost |
|----------|----------|--------------|---------------|------------|
| **Buggy deploy** | 15 min | $0-10 | $0 | $0-10 |
| **Database corruption** | 1-2 hours | $50-200 | $0 | $50-200 |
| **Full outage** | 4-8 hours | $500-2,000 | $100-500 | $600-2,500 |
| **Data loss (no backup)** | 1-3 days | $5,000+ | $1,000+ | $6,000+ |

**Prevention investment:** $50-100/month (backups, monitoring)
**ROI:** Prevents $500-2,500 losses

---

## Next Steps

1. ✅ Set up automated daily backups (Supabase Pro)
2. ✅ Test restore procedure monthly
3. ✅ Document all recovery procedures
4. ✅ Create status page for users
5. ✅ Schedule quarterly disaster recovery drill

**See also:**
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Rollback procedures
- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - Early warning system
- [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - Pre-launch verification
