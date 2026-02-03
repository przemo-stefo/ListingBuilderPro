# 🚀 Railway + Vercel Deployment - Prosty Przewodnik

**Czas:** 15-20 minut
**Poziom:** Beginner-friendly ✅
**Koszt start:** $0 (free tiers)

---

## 🎯 Co Będziemy Robić

1. Push kodu na GitHub (5 min)
2. Deploy backend na Railway (5 min)
3. Deploy frontend na Vercel (3 min)
4. Połącz z domeną (opcjonalnie, 2 min)

**Zero terminala! Wszystko w przeglądarce!** 🎉

---

## 📋 KROK 1: Przygotuj GitHub Repo (5 min)

### A. Stwórz Repo na GitHub

1. Idź do: https://github.com/new
2. Repository name: `marketplace-automation`
3. Private/Public: **Private** (zalecane)
4. Kliknij: **Create repository**

### B. Push Kodu

Na Twoim Macu:

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder

# Initialize git (jeśli jeszcze nie ma)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit - marketplace automation system"

# Add remote
git remote add origin https://github.com/TWOJ-USERNAME/marketplace-automation.git

# Push
git push -u origin main
```

**Uwaga:** Przed push sprawdź że `.env` i `.env.local` są w `.gitignore`!

```bash
# Sprawdź
cat .gitignore | grep "\.env"

# Powinno pokazać:
# .env
# .env.local
# backend/.env
# frontend/.env.local
```

✅ Kod jest na GitHub!

---

## 🚂 KROK 2: Deploy Backend na Railway (5 min)

### A. Stwórz Konto Railway

1. Idź do: https://railway.app
2. Kliknij: **Start a New Project**
3. Zaloguj się przez GitHub (autoryzuj)
4. Dostaniesz: **$5 credit** (wystarczy na ~1 miesiąc testów)

### B. Stwórz Projekt

1. Kliknij: **+ New Project**
2. Wybierz: **Deploy from GitHub repo**
3. Wybierz: `marketplace-automation` (Twoje repo)
4. Kliknij: **Deploy Now**

Railway wykryje automatycznie że to Python + FastAPI!

### C. Configure Backend

1. Kliknij na deployment
2. Idź do: **Variables** (tab)
3. Dodaj zmienne (skopiuj z `backend/.env`):

```bash
# App Config
APP_ENV=production
APP_DEBUG=False
CORS_ORIGINS=https://TWOJA-DOMENA.vercel.app

# Database - Railway Postgres (dodamy za moment)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis - Railway Redis (dodamy za moment)
REDIS_URL=${{Redis.REDIS_URL}}

# API Keys (skopiuj z backend/.env)
GROQ_API_KEY=your_groq_api_key_here
API_SECRET_KEY=generate_with_python_secrets_token_urlsafe_32
WEBHOOK_SECRET=generate_with_python_secrets_token_urlsafe_32

# Marketplace APIs (opcjonalne - dodaj później)
AMAZON_REFRESH_TOKEN=
AMAZON_CLIENT_ID=
AMAZON_CLIENT_SECRET=
EBAY_APP_ID=
KAUFLAND_CLIENT_KEY=
```

### D. Dodaj PostgreSQL Database

1. W Railway project kliknij: **+ New**
2. Wybierz: **Database** → **PostgreSQL**
3. Railway automatycznie:
   - Stworzy database
   - Połączy z backendem
   - Ustawi `DATABASE_URL` variable

4. Otwórz database
5. Kliknij: **Data** tab
6. Kliknij: **Query**
7. Skopiuj i wklej: `/backend/migrations/001_initial_schema.sql`
8. Kliknij: **Execute**

✅ Tabele utworzone!

### E. Dodaj Redis (opcjonalnie - dla background jobs)

1. Kliknij: **+ New**
2. Wybierz: **Database** → **Redis**
3. Railway automatycznie połączy

### F. Configure Root Directory

Railway musi wiedzieć że backend jest w `/backend` folderze:

1. Idź do: **Settings** tab
2. **Root Directory:** `/backend`
3. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Kliknij: **Save**

### G. Deploy!

Railway automatycznie redeploy po zapisaniu settings.

Czekaj ~2 minuty...

✅ Backend deployed!

**Twój URL:** `https://xxx.up.railway.app`

### H. Test Backend

```bash
curl https://xxx.up.railway.app/health
```

**Oczekiwane:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

---

## ▲ KROK 3: Deploy Frontend na Vercel (3 min)

### A. Stwórz Konto Vercel

1. Idź do: https://vercel.com/signup
2. Zaloguj się przez GitHub (autoryzuj)

### B. Import Project

1. Kliknij: **Add New** → **Project**
2. Wybierz: `marketplace-automation` (Twoje repo)
3. Kliknij: **Import**

### C. Configure Frontend

Vercel wykryje Next.js automatycznie!

**Framework Preset:** Next.js ✅
**Root Directory:** `frontend` (ważne!)

**Build settings (auto-detect):**
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

Kliknij: **Advanced** → dodaj Environment Variables:

```bash
NEXT_PUBLIC_API_URL=https://twoj-backend.up.railway.app
NEXT_PUBLIC_API_KEY=generate_with_python_secrets_token_urlsafe_32
```

**⚠️ WAŻNE:**
- Skopiuj dokładny URL z Railway (z kroku 2)
- API_KEY musi być IDENTYCZNY jak `API_SECRET_KEY` w Railway

### D. Deploy!

Kliknij: **Deploy**

Vercel zbudujeXML ~2-3 minuty...

✅ Frontend deployed!

**Twój URL:** `https://marketplace-automation.vercel.app`

### E. Test Frontend

Otwórz w przeglądarce:
```
https://marketplace-automation.vercel.app
```

Powinieneś zobaczyć dashboard! 🎉

---

## 🔄 KROK 4: Update CORS (2 min)

Teraz musisz powiedzieć backendowi że może przyjmować requesty z frontendu.

### W Railway:

1. Idź do backend service
2. **Variables** tab
3. Znajdź: `CORS_ORIGINS`
4. Zmień na: `https://marketplace-automation.vercel.app`
5. Kliknij: **Save**

Railway automatycznie redeploy (~1 min).

✅ CORS skonfigurowany!

---

## 🌐 KROK 5: Custom Domain (Opcjonalnie, 5 min)

### A. Dodaj Domenę do Vercel (Frontend)

Jeśli masz swoją domenę (np. `mojadomena.com`):

1. W Vercel project idź do: **Settings** → **Domains**
2. Dodaj: `mojadomena.com`
3. Vercel pokaże DNS records do ustawienia

**U swojego dostawcy domeny (np. home.pl):**
```
A record:     @              → 76.76.21.21 (Vercel IP)
CNAME record: www            → cname.vercel-dns.com
```

Czekaj 5-30 minut na propagację DNS.

### B. Dodaj Domenę do Railway (Backend API)

1. W Railway project idź do: **Settings** → **Domains**
2. Kliknij: **Generate Domain** (dostaniesz: xxx.up.railway.app)
3. Lub dodaj custom: `api.mojadomena.com`

**U swojego dostawcy domeny:**
```
CNAME record: api → xxx.up.railway.app
```

### C. Update Environment Variables

**W Railway (backend):**
```bash
CORS_ORIGINS=https://mojadomena.com,https://www.mojadomena.com
```

**W Vercel (frontend):**
```bash
NEXT_PUBLIC_API_URL=https://api.mojadomena.com
```

Redeploy obu (auto po zapisaniu).

✅ Custom domain działa!

---

## 🧪 Test Całego Systemu (2 min)

### Test 1: Health Check

```bash
curl https://api.mojadomena.com/health
# lub
curl https://xxx.up.railway.app/health
```

### Test 2: Import Produktu

```bash
curl -X POST https://xxx.up.railway.app/api/import/product \
  -H "X-API-Key: generate_with_python_secrets_token_urlsafe_32" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "raw_data": {
      "title": "Test Product",
      "price": "99.99",
      "ean": "1234567890123"
    }
  }'
```

### Test 3: Frontend

Otwórz: `https://marketplace-automation.vercel.app`

1. Kliknij: **Products**
2. Powinieneś zobaczyć testowy produkt!

---

## 💰 Koszty

### Free Tier (Start):

**Railway:**
- $5 credit miesięcznie (wystarczy na ~500 hours)
- Backend + Database + Redis

**Vercel:**
- 100% darmowy dla hobby projects
- Unlimited deployments
- Custom domain included

**Total: $0/miesiąc** (dopóki mieścisz się w free tier)

### Paid (Production):

**Railway:**
- Pay per usage
- ~$20-30/msc dla małego projektu
- Rośnie z ruchem

**Vercel Pro:**
- $20/msc
- Unlimited bandwidth
- Advanced analytics

**Total: ~$40-50/msc** (~160-200 PLN)

---

## 🔄 Continuous Deployment (Auto-Deploy)

**Już działa!** 🎉

Każdy `git push` automatycznie:

1. **Railway** - redeploy backend
2. **Vercel** - redeploy frontend

```bash
# Na Twoim Macu
git add .
git commit -m "Update feature X"
git push

# Railway i Vercel automatycznie deploy!
# Czekaj ~2-3 minuty i zmiany są live!
```

---

## 📊 Monitoring

### Railway Monitoring:

1. Idź do: Railway Dashboard
2. **Metrics** tab pokazuje:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

### Vercel Analytics:

1. Idź do: Vercel Dashboard
2. **Analytics** tab pokazuje:
   - Page views
   - Response times
   - Top pages
   - Geography (skąd ruch)

---

## 🔧 Troubleshooting

### Problem: Frontend 401 Unauthorized

**Przyczyna:** API keys się nie zgadzają

**Fix:**
1. Railway → Backend → Variables → sprawdź `API_SECRET_KEY`
2. Vercel → Frontend → Settings → Environment Variables → sprawdź `NEXT_PUBLIC_API_KEY`
3. Muszą być IDENTYCZNE!
4. Redeploy frontend jeśli zmieniłeś

### Problem: CORS Error w przeglądarce

**Przyczyna:** CORS_ORIGINS nie zawiera URL frontendu

**Fix:**
1. Railway → Backend → Variables
2. `CORS_ORIGINS=https://twoj-frontend.vercel.app`
3. Redeploy

### Problem: Database connection failed

**Przyczyna:** Nie uruchomiłeś SQL migration

**Fix:**
1. Railway → PostgreSQL database
2. **Data** tab → **Query**
3. Wklej: `backend/migrations/001_initial_schema.sql`
4. Execute
5. Redeploy backend

### Problem: Build Failed (Vercel)

**Przyczyna:** Błąd w kodzie lub brakujące dependencies

**Fix:**
1. Vercel → Deployment → **Logs**
2. Zobacz błąd
3. Napraw lokalnie
4. `git push` (auto-redeploy)

---

## 🎯 Checklist Deployment

- [ ] Kod na GitHub
- [ ] Railway account created
- [ ] Backend deployed na Railway
- [ ] PostgreSQL database added
- [ ] Redis added (opcjonalnie)
- [ ] SQL migration executed
- [ ] Backend environment variables configured
- [ ] Vercel account created
- [ ] Frontend deployed na Vercel
- [ ] Frontend environment variables configured
- [ ] CORS_ORIGINS updated
- [ ] Health check działa
- [ ] Frontend pokazuje dashboard
- [ ] Test import produktu działa
- [ ] (Opcjonalnie) Custom domain configured

---

## 📚 Dodatkowe Resources

### Railway:
- Docs: https://docs.railway.app
- Pricing: https://railway.app/pricing
- Status: https://status.railway.app

### Vercel:
- Docs: https://vercel.com/docs
- Pricing: https://vercel.com/pricing
- Status: https://www.vercel-status.com

---

## 🚀 Next Steps

### 1. Setup Monitoring (Sentry)

Darmowy error tracking:

**Railway (backend):**
```bash
# Variables
SENTRY_DSN=https://xxx@sentry.io/xxx
```

**Vercel (frontend):**
```bash
# Variables
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 2. Add Marketplace Credentials

Gdy będziesz gotowy do publishowania:

**Railway → Variables:**
```bash
AMAZON_REFRESH_TOKEN=...
EBAY_APP_ID=...
KAUFLAND_CLIENT_KEY=...
```

### 3. Setup Backup

Railway automatycznie backupuje database, ale:

**Manual backup (opcjonalnie):**
```bash
# Railway CLI
railway login
railway link
railway run pg_dump > backup.sql
```

### 4. Add Team Members

**Railway:**
- Settings → Members → Invite

**Vercel:**
- Settings → Team → Invite

---

## 💡 Pro Tips

### Tip 1: Preview Deployments

Każdy branch automatycznie dostaje preview URL!

```bash
git checkout -b feature-x
git push origin feature-x

# Vercel automatycznie tworzy:
# https://marketplace-automation-git-feature-x.vercel.app
```

### Tip 2: Environment-Specific Variables

**Production:**
```bash
NEXT_PUBLIC_API_URL=https://api.production.com
```

**Preview (branches):**
```bash
NEXT_PUBLIC_API_URL=https://api.staging.com
```

Vercel i Railway supportują environment-specific vars!

### Tip 3: Rollback

Coś popsułeś? Rollback w 1 klik:

**Vercel:**
- Deployments → kliknij poprzedni deployment → Promote to Production

**Railway:**
- Deployments → kliknij poprzedni → Rollback

---

## 🎉 Gratulacje!

System deployed na Railway + Vercel! 🚀

**Co masz:**
- ✅ Backend API (auto-scaling)
- ✅ PostgreSQL database (managed)
- ✅ Redis (managed)
- ✅ Frontend (global CDN)
- ✅ SSL certificates (auto)
- ✅ Monitoring (built-in)
- ✅ Auto-deploy (git push)
- ✅ Professional setup!

**Koszt:**
- Start: $0 (free tiers)
- Production: ~$40-50/msc

**Porównaj z:**
- Mikrus: ~20 PLN/msc (ale musisz znać DevOps)
- AWS: ~$100/msc (complicated)
- Zero setup headaches! ✅

---

**Pytania?** Zobacz `DEPLOYMENT_COMPARISON.md` dla porównania z Mikrusem!
