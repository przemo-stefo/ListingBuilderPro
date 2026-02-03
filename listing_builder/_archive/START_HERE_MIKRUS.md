# 🚀 START HERE - Deployment na Mikrus VPS

**Czas całkowity:** 60 minut (15 min local + 45 min Mikrus)
**Koszt:** ~24 PLN/miesiąc
**Poziom:** Beginner-friendly ✅

---

## 📍 Gdzie Jesteś Teraz

System jest **gotowy do deployu** z pełnym zabezpieczeniem (Phase 1 security fixes):
- ✅ API key authentication
- ✅ Security headers
- ✅ HTTPS redirect
- ✅ Strong secrets generated
- ✅ Frontend configured
- ✅ Backend secured

**Co zostało:**
- ⚙️ Local setup (15 minut)
- 🚀 Deploy na Mikrus (45 minut)

---

## ⚡ KROK 1: Local Setup (15 minut)

### Automatyczny Setup (Recommended)

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder

# Uruchom automatyczny setup
./auto_setup.sh
```

**Co zrobi auto_setup.sh:**
1. Utworzy backend venv
2. Zainstaluje Python dependencies
3. Zainstaluje frontend dependencies
4. Poprosi Cię o wykonanie SQL migration

### Manual Database Migration (2 minuty)

Po uruchomieniu `auto_setup.sh`, będziesz musiał ręcznie wykonać SQL migration:

1. Otwórz: https://supabase.com/dashboard/project/YOUR_SUPABASE_PROJECT_REF
2. Kliknij: **SQL Editor** (lewe menu)
3. Kliknij: **New query**
4. Skopiuj całą zawartość pliku: `backend/migrations/001_initial_schema.sql`
5. Wklej do SQL Editor
6. Kliknij: **Run**

**Co utworzy:** 6 tabel (products, import_jobs, bulk_jobs, sync_logs, webhooks, webhook_logs)

### Weryfikacja Local Setup

```bash
./setup_check.sh
```

**Oczekiwane:**
```
🎉 PERFECT! Everything is configured correctly!
```

### Test Localnie

```bash
./start_all.sh
```

Otwórz: http://localhost:3000

**Jeśli działa lokalnie → przejdź do Kroku 2 (Mikrus deployment)**

---

## 🇵🇱 KROK 2: Deploy na Mikrus VPS (45 minut)

### A. Kup Mikrus Serwer (5 minut)

1. Idź do: https://mikr.us
2. Wybierz: **Mikrus 2.0** (~20 PLN/msc)
   - 2 GB RAM
   - 20 GB SSD
   - 1 vCPU
   - Unlimited transfer
3. **System:** Ubuntu 22.04 LTS
4. Kup i zapisz:
   - IP adres serwera
   - Root password (dostaniesz mailem)

**Czekaj 5-10 minut na setup serwera.**

### B. Połącz się z Serwerem (2 minuty)

Na Twoim Macu:

```bash
ssh root@TWÓJ-IP-SERWERA
```

Wpisz password z maila.

### C. Install Docker (5 minut)

Na serwerze Mikrus:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify
docker --version
docker-compose --version
```

### D. Upload Projektu na Mikrus (5 minut)

**Na Twoim Macu** (nowe terminal):

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder

# Pack project (exclude node_modules, venv)
tar --exclude='backend/venv' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/.next' \
    --exclude='.git' \
    -czf project.tar.gz .

# Upload to Mikrus
scp project.tar.gz root@TWÓJ-IP:/root/

# Clean up
rm project.tar.gz
```

**Na serwerze Mikrus:**

```bash
cd /root
tar -xzf project.tar.gz
rm project.tar.gz
ls -la
```

### E. Configure Environment (3 minut)

**Na serwerze Mikrus:**

Backend .env już istnieje (skopiowany z Twojego Maca), ale zaktualizuj URL:

```bash
cd /root/backend
nano .env
```

Zmień/dodaj:
```bash
APP_ENV=production
APP_DEBUG=False
CORS_ORIGINS=https://TWOJA-DOMENA.pl,http://TWOJE-IP

# Reszta zostaje bez zmian (Supabase, Groq, secrets)
```

Frontend .env.local:

```bash
cd /root/frontend
nano .env.local
```

Zmień:
```bash
NEXT_PUBLIC_API_URL=http://TWOJE-IP
NEXT_PUBLIC_API_KEY=generate_with_python_secrets_token_urlsafe_32
```

### F. Create Docker Compose (8 minut)

**Na serwerze Mikrus:**

```bash
cd /root
nano docker-compose.yml
```

Wklej:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: listing_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
      - /app/venv
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
    networks:
      - app-network
    depends_on:
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: listing_frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env.local
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    networks:
      - app-network
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    container_name: listing_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: listing_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - app-network
    depends_on:
      - backend
      - frontend

volumes:
  redis-data:

networks:
  app-network:
    driver: bridge
```

### G. Create Dockerfiles

**Backend Dockerfile:**

```bash
cd /root/backend
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Frontend Dockerfile:**

```bash
cd /root/frontend
nano Dockerfile
```

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy app
COPY . .

# Build
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### H. Setup Nginx (5 minut)

**Na serwerze Mikrus:**

```bash
cd /root
nano nginx.conf
```

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name TWOJE-IP;

        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support (dla Next.js hot reload)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

Zmień `TWOJE-IP` na rzeczywisty IP Mikrusa.

### I. Deploy! (5 minut)

**Na serwerze Mikrus:**

```bash
cd /root

# Build and start
docker-compose up -d --build

# Sprawdź status
docker-compose ps

# Sprawdź logi
docker-compose logs -f
```

**Czekaj ~3-5 minut na build i start.**

### J. Test Deployment

```bash
# Health check
curl http://TWOJE-IP/health

# Otwórz w przeglądarce
# http://TWOJE-IP
```

**Jeśli widzisz dashboard → DZIAŁA!** 🎉

---

## 🌐 KROK 3: Dodaj Domenę (Opcjonalnie, 10 minut)

Jeśli masz domenę (np. `mojadomena.pl`):

### A. Kup Domenę (jeśli nie masz)

1. Idź do: https://home.pl
2. Kup domenę (~4 PLN/msc)
3. Zapisz dane dostępowe do panelu

### B. Ustaw DNS

W panelu home.pl (lub innego dostawcy):

```
A record:     @              → TWOJE-IP-MIKRUSA
A record:     www            → TWOJE-IP-MIKRUSA
```

Czekaj 5-30 minut na propagację DNS.

### C. Update Nginx z Domeną

**Na serwerze Mikrus:**

```bash
cd /root
nano nginx.conf
```

Zmień:
```nginx
server_name mojadomena.pl www.mojadomena.pl;
```

Restart:
```bash
docker-compose restart nginx
```

### D. Setup SSL (Let's Encrypt) - 5 minut

**Na serwerze Mikrus:**

```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Stop nginx container temporarily
docker-compose stop nginx

# Get certificate
certbot certonly --standalone -d mojadomena.pl -d www.mojadomena.pl

# Certificates saved to: /etc/letsencrypt/live/mojadomena.pl/
```

Update nginx.conf z HTTPS:

```nginx
server {
    listen 80;
    server_name mojadomena.pl www.mojadomena.pl;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mojadomena.pl www.mojadomena.pl;

    ssl_certificate /etc/letsencrypt/live/mojadomena.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mojadomena.pl/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... reszta konfiguracji (location blocks)
}
```

Mount SSL certs w docker-compose.yml:

```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro  # Add this
```

Restart:
```bash
docker-compose up -d
```

Test:
```
https://mojadomena.pl
```

### E. Auto-Renew SSL (Certbot Cron)

```bash
# Test renewal
certbot renew --dry-run

# Add cron job (runs daily at 3am)
crontab -e
```

Add:
```
0 3 * * * certbot renew --quiet && docker-compose restart nginx
```

---

## ✅ Checklist Deployment

- [ ] Mikrus VPS zakupiony
- [ ] SSH connection działa
- [ ] Docker zainstalowany
- [ ] Projekt uploaded
- [ ] .env files skonfigurowane
- [ ] docker-compose.yml created
- [ ] Dockerfiles created
- [ ] nginx.conf created
- [ ] `docker-compose up -d --build` wykonane
- [ ] Health check działa
- [ ] Frontend otwiera się w przeglądarce
- [ ] (Opcjonalnie) Domena ustawiona
- [ ] (Opcjonalnie) SSL zainstalowany

---

## 🔧 Troubleshooting

### Problem: Container nie startuje

```bash
# Sprawdź logi
docker-compose logs backend
docker-compose logs frontend

# Restart
docker-compose restart
```

### Problem: Port already in use

```bash
# Sprawdź co używa portu
netstat -tuln | grep 8000

# Kill process
kill -9 PID
```

### Problem: Frontend 401 Unauthorized

**Sprawdź czy API keys się zgadzają:**

```bash
# Backend
cat /root/backend/.env | grep API_SECRET_KEY

# Frontend
cat /root/frontend/.env.local | grep NEXT_PUBLIC_API_KEY

# Muszą być IDENTYCZNE!
```

### Problem: Database connection failed

**Sprawdź czy SQL migration była wykonana:**

1. Otwórz: https://supabase.com/dashboard/project/YOUR_SUPABASE_PROJECT_REF
2. Kliknij: **Table Editor**
3. Sprawdź czy widzisz 6 tabel

Jeśli nie → wróć do Kroku 1 (Manual Database Migration)

---

## 🔄 Update Code na Mikrus

Gdy zmienisz kod lokalnie:

**Na Twoim Macu:**

```bash
cd /Users/shawn/Projects/ListingBuilderPro/listing_builder

# Pack updated code
tar --exclude='backend/venv' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/.next' \
    --exclude='.git' \
    -czf project.tar.gz .

# Upload
scp project.tar.gz root@TWÓJ-IP:/root/

# SSH into Mikrus
ssh root@TWÓJ-IP
```

**Na serwerze Mikrus:**

```bash
cd /root

# Backup current (optional)
mv backend backend.backup
mv frontend frontend.backup

# Extract new code
tar -xzf project.tar.gz
rm project.tar.gz

# Rebuild and restart
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

---

## 📊 Monitoring

### Check System Status

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Recent logs
docker-compose logs --tail=100 -f

# Disk space
df -h
```

### Backup Database (Recommended)

Supabase automatycznie backupuje, ale możesz też manualnie:

1. Supabase Dashboard → Database → Backups
2. Kliknij: **Create Backup**

---

## 💰 Koszt

| Pozycja | Koszt |
|---------|-------|
| Mikrus 2.0 VPS | ~20 PLN/msc |
| Domena (opcjonalnie) | ~4 PLN/msc |
| SSL (Let's Encrypt) | Darmowy |
| **TOTAL** | **~24 PLN/msc** |

**Supabase:** Free tier (wystarczy na start)
**Groq API:** Darmowy (1M tokens/day)

---

## 🎯 Podsumowanie

**Masz teraz:**
- ✅ System deployed na Mikrus VPS
- ✅ Docker containerization
- ✅ Nginx reverse proxy
- ✅ Redis dla background jobs
- ✅ Production-ready security (Phase 1)
- ✅ SSL (jeśli domena)
- ✅ Auto-restart containers
- ✅ Koszt: ~24 PLN/msc

**URLs:**
- Frontend: http://TWOJE-IP (lub https://mojadomena.pl)
- API: http://TWOJE-IP/api
- Health: http://TWOJE-IP/health

---

## 📚 Dodatkowe Resources

**Szczegółowa dokumentacja:**
- `MIKRUS_DEPLOYMENT.md` - Kompletny przewodnik (3500 linii)
- `SETUP_COMPLETE_GUIDE.md` - Local setup
- `SECURITY_FIXES_APPLIED.md` - Security details

**Komendy pomocnicze:**
- `./setup_check.sh` - Weryfikacja local setup
- `./auto_setup.sh` - Automatyczny local setup
- `./start_all.sh` - Start lokalnie

---

## 🚀 Next Steps

1. **Setup lokalnie** (15 min): `./auto_setup.sh`
2. **Test lokalnie** (2 min): `./start_all.sh` + http://localhost:3000
3. **Deploy na Mikrus** (45 min): Follow Krok 2
4. **Dodaj domenę** (opcjonalnie, 10 min): Follow Krok 3

**Jeśli masz pytania podczas setup → pisz!**

---

**To jest JEDYNA rekomendowana ścieżka deployment dla tego projektu.** 🇵🇱
