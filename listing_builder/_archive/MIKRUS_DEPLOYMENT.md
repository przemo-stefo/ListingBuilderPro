# 🇵🇱 Deployment na Mikrus VPS - Kompletny Przewodnik

**Mikrus:** Tani polski VPS (~10-40 PLN/miesiąc)
**Czas setup:** 30-45 minut
**Poziom:** Średni (wymaga terminala)

---

## 💰 Krok 1: Zakup Serwera Mikrus (5 min)

### Gdzie Kupić

https://mikr.us/

### Rekomendowane Pakiety

| Pakiet | CPU | RAM | Dysk | Cena | Dla Czego |
|--------|-----|-----|------|------|-----------|
| **Mikrus 1.0** | 1 vCore | 1 GB | 10 GB | ~10 PLN | Development/Test |
| **Mikrus 2.0** | 2 vCore | 2 GB | 20 GB | ~20 PLN | **RECOMMENDED** |
| **Mikrus 3.0** | 3 vCore | 4 GB | 40 GB | ~40 PLN | Production (100+ users) |

**Zalecany dla tego projektu:** **Mikrus 2.0** (2 GB RAM)

### Dlaczego Mikrus 2.0?

- ✅ 2 GB RAM = Backend + Frontend + Database + Redis
- ✅ 2 vCores = Wystarczy dla 50-100 concurrent users
- ✅ 20 GB dysku = System + Kod + Logi + Database
- ✅ ~20 PLN/miesiąc = Najtańsza opcja z sensem

### Co Dostaniesz

Po zakupie:
- IP serwera: `xxx.xxx.xxx.xxx`
- SSH access: `ssh root@xxx.xxx.xxx.xxx`
- Password: (dostaniesz mailem)

---

## 🔧 Krok 2: Pierwsza Konfiguracja Serwera (10 min)

### Połącz Się z Serwerem

```bash
# Z Twojego Maca
ssh root@xxx.xxx.xxx.xxx

# Wpisz password (dostałeś mailem)
# Jesteś teraz na serwerze Mikrus!
```

### Zaktualizuj System

```bash
# Ubuntu/Debian commands
apt update
apt upgrade -y
apt install -y curl wget git vim nginx certbot python3-certbot-nginx
```

### Zainstaluj Docker (Najłatwiejszy Sposób)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Sprawdź instalację
docker --version
docker-compose --version
```

---

## 📦 Krok 3: Przygotuj Projekt na Serwerze (5 min)

### Stwórz Folder Projektu

```bash
# Na serwerze Mikrus
mkdir -p /opt/marketplace
cd /opt/marketplace
```

### Opcja A: Git Clone (Jeśli Masz GitHub)

```bash
# Jeśli projekt jest na GitHub
git clone https://github.com/twoj-username/marketplace-automation.git .

# Lub skopiuj z lokalnego (z Twojego Maca):
# scp -r /Users/shawn/Projects/ListingBuilderPro/listing_builder/* root@xxx.xxx.xxx.xxx:/opt/marketplace/
```

### Opcja B: Ręczne Upload (Bez GitHub)

Na Twoim Macu:

```bash
# Spakuj projekt
cd /Users/shawn/Projects/ListingBuilderPro
tar -czf listing_builder.tar.gz listing_builder/

# Upload na serwer
scp listing_builder.tar.gz root@xxx.xxx.xxx.xxx:/opt/

# Na serwerze rozpakuj
ssh root@xxx.xxx.xxx.xxx
cd /opt
tar -xzf listing_builder.tar.gz
mv listing_builder marketplace
cd marketplace
```

---

## 🐳 Krok 4: Docker Deployment (Najłatwiejszy)

### Stwórz Produkcyjny docker-compose.yml

Na serwerze w `/opt/marketplace/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: marketplace
      POSTGRES_USER: marketplace
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations/001_initial_schema.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U marketplace"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Queue
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      APP_ENV: production
      APP_DEBUG: 'False'
      DATABASE_URL: postgresql://marketplace:${DB_PASSWORD}@postgres:5432/marketplace
      REDIS_URL: redis://redis:6379/0
      GROQ_API_KEY: ${GROQ_API_KEY}
      API_SECRET_KEY: ${API_SECRET_KEY}
      WEBHOOK_SECRET: ${WEBHOOK_SECRET}
      CORS_ORIGINS: https://${DOMAIN}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # AI Worker (Background Jobs)
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: dramatiq workers.ai_worker
    environment:
      DATABASE_URL: postgresql://marketplace:${DB_PASSWORD}@postgres:5432/marketplace
      REDIS_URL: redis://redis:6379/0
      GROQ_API_KEY: ${GROQ_API_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - app_network

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: https://api.${DOMAIN}
        NEXT_PUBLIC_API_KEY: ${API_SECRET_KEY}
    restart: always
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### Stwórz Backend Dockerfile

`/opt/marketplace/backend/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Stwórz Frontend Dockerfile

`/opt/marketplace/frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build arguments
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_API_KEY

# Build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production

# Run as non-root
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
```

### Stwórz Nginx Config

`/opt/marketplace/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=30r/s;

    # Upstream services
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # API Server (api.yourdomain.com)
    server {
        listen 80;
        server_name api.yourdomain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        # SSL certificates (Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # Frontend (yourdomain.com)
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Rate limiting
        limit_req zone=web burst=50 nodelay;

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Stwórz .env dla Produkcji

`/opt/marketplace/.env.prod`:

```bash
# Database
DB_PASSWORD=generate-strong-password-here

# API Keys
GROQ_API_KEY=your_groq_api_key_here
API_SECRET_KEY=generate_with_python_secrets_token_urlsafe_32
WEBHOOK_SECRET=generate_with_python_secrets_token_urlsafe_32

# Domain
DOMAIN=yourdomain.com
```

---

## 🌐 Krok 5: Domena i SSL (10 min)

### Ustaw DNS (u Swojego Dostawcy Domeny)

```
A record:     yourdomain.com     → xxx.xxx.xxx.xxx (IP Mikrus)
A record: www.yourdomain.com     → xxx.xxx.xxx.xxx
A record: api.yourdomain.com     → xxx.xxx.xxx.xxx
```

Czekaj 5-30 minut na propagację DNS.

### Sprawdź Propagację

```bash
# Z Twojego Maca
nslookup yourdomain.com
# Powinno zwrócić IP serwera Mikrus
```

### Wygeneruj SSL (Let's Encrypt - DARMOWY)

Na serwerze Mikrus:

```bash
# Zatrzymaj nginx jeśli działa
systemctl stop nginx

# Wygeneruj certyfikaty
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Odpowiedz na pytania:
# Email: twoj@email.com
# Agree to ToS: Yes (A)
# Share email: No (N)

# Certyfikaty zapisane w:
# /etc/letsencrypt/live/yourdomain.com/
```

### Auto-Renewal SSL

```bash
# Certbot automatycznie dodaje cron job
# Sprawdź czy działa:
certbot renew --dry-run

# Jeśli OK - certyfikaty będą automatycznie odnawiane co 90 dni
```

---

## 🚀 Krok 6: Deploy! (5 min)

### Build i Uruchom

```bash
cd /opt/marketplace

# Load environment variables
export $(cat .env.prod | xargs)

# Build and start wszystko
docker-compose -f docker-compose.prod.yml up -d --build

# To zajmie 5-10 minut (building images)
```

### Sprawdź Status

```bash
# Zobacz czy wszystko działa
docker-compose -f docker-compose.prod.yml ps

# Powinno pokazać:
# postgres   Up (healthy)
# redis      Up (healthy)
# backend    Up (healthy)
# worker     Up
# frontend   Up (healthy)
# nginx      Up
```

### Sprawdź Logi (Jeśli Coś Nie Działa)

```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# All logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🧪 Krok 7: Testowanie (5 min)

### Test 1: Health Check

```bash
curl https://api.yourdomain.com/health
```

**Oczekiwane:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### Test 2: Frontend

Otwórz w przeglądarce:
```
https://yourdomain.com
```

Powinieneś zobaczyć dashboard.

### Test 3: Import Produktu

```bash
curl -X POST https://api.yourdomain.com/api/import/product \
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

---

## 📊 Monitoring i Maintenance

### Sprawdź Zużycie Zasobów

```bash
# CPU i RAM
docker stats

# Disk usage
df -h
du -sh /opt/marketplace
du -sh /var/lib/docker
```

### Backup Database

```bash
# Manual backup
docker exec marketplace_postgres_1 pg_dump -U marketplace marketplace > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i marketplace_postgres_1 psql -U marketplace marketplace < backup_20260123.sql
```

### View Logs

```bash
# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs backend -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Update and restart
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 💰 Koszty Mikrus

### Miesięczne Koszty

| Item | Koszt |
|------|-------|
| Mikrus 2.0 VPS | ~20 PLN |
| Domena (.com) | ~50 PLN/rok = ~4 PLN/msc |
| SSL (Let's Encrypt) | Darmowe! |
| **TOTAL** | **~24 PLN/miesiąc** |

### Porównanie z Alternatywami

| Provider | Koszt (EUR) | Koszt (PLN) |
|----------|-------------|-------------|
| **Mikrus 2.0** | ~€5 | ~20 PLN ✅ Najtaniej! |
| Railway | €20 | ~80 PLN |
| Vercel Pro | €20 | ~80 PLN |
| DigitalOcean | €12 | ~50 PLN |
| Hetzner | €5 | ~20 PLN |

**Mikrus = Najtańszy dla Polaków!** 🇵🇱

---

## 🆘 Troubleshooting

### Backend nie łączy z database

**Sprawdź:**
```bash
docker-compose -f docker-compose.prod.yml logs postgres
docker-compose -f docker-compose.prod.yml logs backend
```

**Fix:**
```bash
# Restart database
docker-compose -f docker-compose.prod.yml restart postgres

# Wait for health check
docker-compose -f docker-compose.prod.yml ps
```

### Frontend 502 Bad Gateway

**Przyczyna:** Frontend nie działa

**Fix:**
```bash
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### SSL nie działa

**Sprawdź:**
```bash
ls /etc/letsencrypt/live/yourdomain.com/
# Powinno pokazać: fullchain.pem, privkey.pem

# Test certyfikatu
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -noout -text
```

### Brak miejsca na dysku

```bash
# Sprawdź
df -h

# Wyczyść Docker
docker system prune -a --volumes

# Wyczyść logi
docker-compose -f docker-compose.prod.yml logs --tail=0
```

---

## 🎯 Checklist Deployment

- [ ] Kupiony serwer Mikrus (2.0 recommended)
- [ ] Zainstalowany Docker + Docker Compose
- [ ] Projekt uploaded na serwer
- [ ] Skonfigurowany `.env.prod`
- [ ] DNS ustawione (A records)
- [ ] SSL certyfikaty wygenerowane (Let's Encrypt)
- [ ] Nginx config zaktualizowany (domena)
- [ ] `docker-compose up -d --build` uruchomione
- [ ] Health check działa
- [ ] Frontend dostępny przez HTTPS
- [ ] Backend API działa
- [ ] Database połączona

---

**Pytania?** Zobacz `DEPLOYMENT_GUIDE.md` dla innych opcji (Railway, Vercel).

🚀 **Powodzenia z Mikrusem!** 🇵🇱
