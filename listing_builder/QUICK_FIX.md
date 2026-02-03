# ⚡ Ultra Szybki Fix - 3 Komendy

**Czas:** 5 minut

---

## 🔧 Co Naprawić (według ./setup_check.sh)

### ❌ Problem 1: Backend venv

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ Problem 2: Frontend dependencies

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder/frontend
npm install
```

### ❌ Problem 3: Database tables

1. Otwórz: https://supabase.com/dashboard/project/YOUR_SUPABASE_PROJECT_REF
2. Kliknij: **SQL Editor** (lewe menu)
3. Kliknij: **New query**
4. Skopiuj cały plik: `backend/migrations/001_initial_schema.sql`
5. Wklej i kliknij: **Run**

---

## ✅ Sprawdź Że Działa

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder
./setup_check.sh
```

Powinno pokazać:
```
🎉 PERFECT! Everything is configured correctly!
```

---

## 🚀 Uruchom

```bash
./start_all.sh
```

Otwórz: http://localhost:3000

---

**To wszystko!** 🎉

Szczegóły: zobacz `SETUP_COMPLETE_GUIDE.md`
