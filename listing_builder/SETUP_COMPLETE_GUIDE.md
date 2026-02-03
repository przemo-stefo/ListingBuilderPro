# 🔧 Kompletny Przewodnik Setup - Krok Po Kroku

**Status sprawdzony:** 2026-01-23
**Czas setup:** 10-15 minut

---

## ⚡ Szybki Check - Co Wymaga Naprawy

Najpierw uruchom:
```bash
./setup_check.sh
```

Pokaże Ci dokładnie co działa (✅), co wymaga uwagi (⚠️), i co jest zepsute (❌).

---

## 📋 KROK 1: Backend Virtual Environment (2 min)

### Problem: ❌ Backend virtual environment

### Rozwiązanie:

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend

# Stwórz venv
python3 -m venv venv

# Aktywuj venv
source venv/bin/activate

# Powinieneś zobaczyć (venv) przed promptem:
# (venv) shawn@Mac backend %

# Zainstaluj dependencies
pip install -r requirements.txt

# To zajmie ~2 minuty, zainstaluje:
# - fastapi, uvicorn
# - sqlalchemy, psycopg2-binary
# - groq, pydantic-settings
# - structlog, redis, dramatiq
# - i inne...
```

**Weryfikacja:**
```bash
# Sprawdź czy FastAPI zainstalowane
python -c "import fastapi; print('FastAPI OK')"

# Powinno wyświetlić: FastAPI OK
```

---

## 📋 KROK 2: Frontend Dependencies (3 min)

### Problem: ❌ Frontend dependencies

### Rozwiązanie:

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/frontend

# Zainstaluj wszystkie dependencies
npm install

# To zajmie ~3 minuty, zainstaluje:
# - next, react, react-dom
# - axios, @tanstack/react-query
# - tailwindcss
# - lucide-react (ikony)
# - i inne...
```

**Weryfikacja:**
```bash
# Sprawdź czy next zainstalowane
ls node_modules/.bin/next

# Powinno pokazać ścieżkę do pliku
```

---

## 📋 KROK 3: Database Setup (5-10 min)

### Problem: ❌ Database connection

**Dobre wieści:** Supabase project ISTNIEJE (DNS resolves)!
**Problem:** Brak tabel w bazie danych.

### Rozwiązanie - Opcja A: Uruchom Migrację SQL (Najszybsze)

1. **Otwórz Supabase Dashboard:**
   ```
   https://supabase.com/dashboard/project/YOUR_SUPABASE_PROJECT_REF
   ```

2. **Przejdź do SQL Editor:**
   - W lewym menu kliknij "SQL Editor"
   - Kliknij "New query"

3. **Skopiuj i Wklej SQL:**
   - Otwórz plik: `backend/migrations/001_initial_schema.sql`
   - Skopiuj CAŁĄ zawartość
   - Wklej do SQL Editor w Supabase
   - Kliknij "Run" (zielony przycisk)

4. **Powinno się wykonać bez błędów**
   - Jeśli sukces - zobaczysz "Success. No rows returned"
   - Tabele utworzone: products, import_jobs, bulk_jobs, sync_logs, webhooks

**Weryfikacja:**
```bash
# Test połączenia (po utworzeniu tabel)
cd backend
source venv/bin/activate
python -c "
from database import check_db_connection
print('Database:', 'Connected' if check_db_connection() else 'Failed')
"

# Powinno wyświetlić: Database: Connected
```

### Rozwiązanie - Opcja B: Nowy Supabase Project (Jeśli A nie działa)

Jeśli stary projekt nie działa, stwórz nowy:

1. **Stwórz Nowy Projekt:**
   - https://supabase.com/dashboard
   - Kliknij "New Project"
   - Name: `marketplace-automation`
   - Database Password: Wygeneruj silne hasło
   - Region: `Europe (eu-central-1)`
   - Kliknij "Create new project" (czeka ~2 min)

2. **Skopiuj Credentials:**
   - Project URL: `https://xxxxx.supabase.co`
   - Anon key: (długi token starting with `eyJ...`)
   - Service role key: (długi token starting with `eyJ...`)

3. **Zaktualizuj backend/.env:**
   ```bash
   SUPABASE_URL=https://twoj-nowy-project.supabase.co
   SUPABASE_KEY=twoj-anon-key
   SUPABASE_SERVICE_KEY=twoj-service-role-key
   DATABASE_URL=postgresql://postgres.twoj-project:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```

4. **Uruchom migrację SQL** (jak w Opcji A, krok 2-4)

---

## 📋 KROK 4: Redis (OPCJONALNY - dla background jobs)

### Problem: ⚠️ Redis server (warning, nie krytyczne)

Redis jest potrzebny TYLKO dla background workers (AI optimization w tle).
Możesz pominąć jeśli chcesz tylko przetestować system.

### Rozwiązanie (jeśli chcesz):

```bash
# Zainstaluj Redis (tylko raz)
brew install redis

# Uruchom Redis server
brew services start redis

# Sprawdź czy działa
redis-cli ping
# Powinno odpowiedzieć: PONG
```

**Bez Redis:**
- ✅ Import produktów działa
- ✅ Lista produktów działa
- ✅ API wszystko działa
- ❌ Background AI optimization nie zadziała (musisz wywołać sync)

**Z Redis:**
- ✅ Wszystko powyżej
- ✅ AI optimization działa w tle (asynchronicznie)

---

## 📋 KROK 5: Weryfikacja Finalna (1 min)

Uruchom ponownie check:

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder
./setup_check.sh
```

**Oczekiwany wynik:**
```
✅ Backend .env file
✅ Python 3.x installed
✅ Backend virtual environment
✅ Backend dependencies
✅ Supabase URL configured
✅ Supabase DNS resolution
✅ Groq API key
✅ API Secret Key
✅ Node.js installed
✅ Frontend .env.local
✅ API keys match
✅ Frontend dependencies
✅ Database migration SQL
✅ Database connection         ← Najważniejsze!
✅ AI Worker file

🎉 PERFECT! Everything is configured correctly!
```

Jeśli Redis nie zainstalowany:
```
⚠️  Redis server
   Not installed. Optional for background jobs.
```
To jest OK - nie jest krytyczne.

---

## 🚀 KROK 6: Uruchom System (30 sekund)

### Opcja A: Auto-start (Najszybsze)

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder
./start_all.sh
```

Uruchomi backend + frontend automatycznie.

### Opcja B: Osobne Terminale (Dla debugowania)

**Terminal 1 - Backend:**
```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/frontend
npm run dev
```

**Terminal 3 - Worker (opcjonalnie, jeśli masz Redis):**
```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend
source venv/bin/activate
dramatiq workers.ai_worker
```

---

## 🧪 KROK 7: Przetestuj Że Działa (2 min)

### Test 1: Backend Health

```bash
curl http://localhost:8000/health
```

**Oczekiwane:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "development"
}
```

### Test 2: API Documentation

Otwórz w przeglądarce:
```
http://localhost:8000/docs
```

Powinieneś zobaczyć interactive API docs (Swagger UI).

### Test 3: Frontend

Otwórz w przeglądarce:
```
http://localhost:3000
```

Powinieneś zobaczyć:
- Dashboard z kartami (Products, Pending, Optimized, Published)
- Nawigację (Products, Optimize, Publish)
- Brak błędów w konsoli (F12)

### Test 4: Import Produktu

```bash
curl -X POST http://localhost:8000/api/import/product \
  -H "X-API-Key: generate_with_python_secrets_token_urlsafe_32" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "raw_data": {
      "title": "Test Product - iPhone 16 Pro",
      "price": "1299.99",
      "ean": "1234567890123",
      "description": "Test description"
    }
  }'
```

**Oczekiwane:**
```json
{
  "id": "uuid-tutaj",
  "title_original": "Test Product - iPhone 16 Pro",
  "status": "imported",
  "source": "test",
  "created_at": "2026-01-23T..."
}
```

### Test 5: Lista Produktów w Frontendzie

1. Odśwież http://localhost:3000
2. Kliknij "Products" w nawigacji
3. Powinieneś zobaczyć testowy produkt na liście

---

## 🎉 SUKCES! Co Teraz?

System działa w 100%! Możesz:

### 1. Zaimportować Więcej Produktów

```bash
curl -X POST http://localhost:8000/api/import/batch \
  -H "X-API-Key: generate_with_python_secrets_token_urlsafe_32" \
  -H "Content-Type: application/json" \
  -d @test_data/valid_products.json
```

### 2. Przetestować AI Optimization

W frontendzie:
1. Przejdź do Products
2. Kliknij na produkt
3. Kliknij "Optimize with AI"
4. Zobacz jak Groq generuje optimized title

### 3. Skonfigurować n8n Webhook

1. W n8n workflow dodaj webhook node
2. URL: `http://localhost:8000/api/import/webhook`
3. Method: POST
4. Headers: `X-Webhook-Secret: generate_with_python_secrets_token_urlsafe_32`
5. Test workflow

### 4. Dodać Marketplace Credentials

Gdy będziesz gotowy do publishowania:

**Amazon SP-API:**
- Zarejestruj się: https://developer-docs.amazon.com/sp-api/
- Dodaj do `backend/.env`:
  ```
  AMAZON_REFRESH_TOKEN=...
  AMAZON_CLIENT_ID=...
  AMAZON_CLIENT_SECRET=...
  ```

**eBay API:**
- Zarejestruj się: https://developer.ebay.com/
- Dodaj credentials do `backend/.env`

**Kaufland API:**
- Zarejestruj się: https://www.kaufland.de/api/
- Dodaj credentials do `backend/.env`

---

## 🆘 Troubleshooting

### Błąd: "ModuleNotFoundError: No module named 'fastapi'"

**Przyczyna:** Nie zainstalowane dependencies lub nie aktywowany venv

**Rozwiązanie:**
```bash
cd backend
source venv/bin/activate  # Ważne!
pip install -r requirements.txt
```

### Błąd: "Connection refused" przy imporcie

**Przyczyna:** Backend nie działa

**Rozwiązanie:**
```bash
# Terminal 1: Sprawdź czy backend działa
curl http://localhost:8000/health

# Jeśli nie odpowiada - uruchom:
cd backend
source venv/bin/activate
python main.py
```

### Błąd: Frontend 401 Unauthorized

**Przyczyna:** API keys się nie zgadzają

**Rozwiązanie:**
```bash
# Sprawdź backend
grep API_SECRET_KEY backend/.env

# Sprawdź frontend
grep NEXT_PUBLIC_API_KEY frontend/.env.local

# Muszą być IDENTYCZNE!
# Jeśli nie - skopiuj z backend/.env do frontend/.env.local
```

### Database nie łączy się

**Rozwiązanie:**
1. Sprawdź czy tabele istnieją w Supabase (SQL Editor → "Tables")
2. Jeśli nie - uruchom migrację (Krok 3)
3. Jeśli dalej nie działa - stwórz nowy projekt (Opcja B)

### Redis connection refused

**To OK!** Redis jest opcjonalny. Jeśli nie używasz background workers, możesz zignorować ten błąd.

**Jeśli chcesz naprawić:**
```bash
brew install redis
brew services start redis
```

---

## 📊 Podsumowanie - Co Musisz Zrobić

### Krytyczne (MUSI być):

1. ✅ **Backend venv** → `cd backend && python3 -m venv venv && pip install -r requirements.txt`
2. ✅ **Frontend deps** → `cd frontend && npm install`
3. ✅ **Database tables** → Uruchom SQL w Supabase SQL Editor

### Opcjonalne (nice to have):

4. ⚠️ **Redis** → `brew install redis && brew services start redis` (dla background jobs)

### Gotowe automatycznie:

- ✅ Backend .env (już skonfigurowany z Twoimi credentials)
- ✅ Frontend .env.local (już skonfigurowany)
- ✅ Security middleware (już dodane)
- ✅ API key authentication (już działa)

---

## ⏱️ Szacowany Czas

| Krok | Czas | Czy Krytyczne |
|------|------|---------------|
| 1. Backend venv + deps | 2 min | ✅ TAK |
| 2. Frontend deps | 3 min | ✅ TAK |
| 3. Database setup | 5 min | ✅ TAK |
| 4. Redis (opcjonalny) | 2 min | ⚠️ NIE |
| 5. Weryfikacja | 1 min | ✅ TAK |
| 6. Uruchomienie | 30 sek | - |
| 7. Testy | 2 min | ✅ TAK |
| **TOTAL** | **~15 min** | - |

---

## 🎯 Quick Commands (Copy-Paste)

Wszystkie komendy w jednym miejscu:

```bash
# Przejdź do projektu
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder

# 1. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 2. Setup frontend
cd frontend
npm install
cd ..

# 3. Check status
./setup_check.sh

# 4. Start system
./start_all.sh
```

**Następnie:** Uruchom migrację SQL w Supabase (Krok 3, manual w przeglądarce).

---

**Pytania?** Uruchom `./setup_check.sh` - pokaże Ci co jeszcze wymaga naprawy!

🚀 **Powodzenia!**
