# Plan Wdrożenia — Pakiet Automatyzacji dla Marcina
**Data:** 2026-02-26 | **Status:** Marcin zainteresowany

---

## FAZA 0 — Infrastruktura (1 dzień)

### Krok 0.1: Gdzie postawić n8n?

**Opcja A: Mikrus dla Marcina (REKOMENDOWANE)**
- Mikrus 1.0 = ~30 PLN/rok, wystarczy na n8n + PostgreSQL
- Docker, pełna kontrola, polska firma
- Shawn konfiguruje, Marcin tylko używa

**Opcja B: VPS (Hetzner/OVH)**
- ~4 EUR/mies za CX22 (2 vCPU, 4GB RAM)
- Więcej mocy, ale drożej

**Opcja C: n8n Cloud**
- Starter 20 EUR/mies — zero konfiguracji
- Najłatwiejsze ale płatne

**Opcja D: Na komputerze Marcina (Docker Desktop)**
- 0 zł ale działa tylko gdy komputer włączony
- OK na testy, nie na produkcję

### Krok 0.2: Domena + tunel (opcjonalne)
- Cloudflare Tunnel → n8n dostępny z zewnątrz (webhook'i!)
- Albo: ngrok (darmowy, ale zmienia URL)
- POTRZEBNE dla: Messenger Bot (#4), Crisis Form (#5), Newsletter Subscribe (#6)

### Krok 0.3: Docker setup
```bash
# Na serwerze
mkdir -p /root/n8n-marcin
cd /root/n8n-marcin

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.example.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.example.com/
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=marcin
      - N8N_BASIC_AUTH_PASSWORD=WYGENERUJ_HASLO
      - GENERIC_TIMEZONE=Europe/Warsaw
      - TZ=Europe/Warsaw
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
EOF

docker compose up -d
```

---

## FAZA 1 — Credentials (2-3 godziny, RAZEM z Marcinem)

Najważniejsza faza. Bez credentials nic nie działa.
Robimy to na jednym call'u (Zoom/Meet) z Marcinem.

### Krok 1.1: Gemini API Key (5 min)
1. Marcin wchodzi na: https://aistudio.google.com
2. Loguje się kontem Google
3. Get API Key → Create API Key
4. Kopiuje klucz (AIza...)
5. W n8n: Settings → Credentials → New → "Query Auth"
   - Name: `Gemini API Key`
   - Name: `key`
   - Value: `AIza...`

### Krok 1.2: Groq API Key (5 min)
1. https://console.groq.com → Sign Up (darmowe)
2. API Keys → Create API Key
3. W n8n: Credentials → New → "Header Auth"
   - Name: `Groq API Key`
   - Header Name: `Authorization`
   - Header Value: `Bearer gsk_...`

### Krok 1.3: Telegram Bot (10 min)
1. Marcin otwiera Telegram → szuka @BotFather
2. /newbot → podaje nazwę: "Radar Radnego"
3. Kopiuje token
4. Pisze cokolwiek do bota
5. Otwiera: https://api.telegram.org/bot<TOKEN>/getUpdates
6. Kopiuje chat_id z odpowiedzi
7. W n8n: Credentials → New → "Telegram API"
   - Access Token: token z BotFather
8. Settings → Variables:
   - `TELEGRAM_CHAT_ID` = skopiowany chat_id

### Krok 1.4: Google Sheets OAuth2 (15 min)
1. https://console.cloud.google.com → New Project: "n8n-marcin"
2. APIs & Services → Enable: Google Sheets API, Gmail API
3. Credentials → Create → OAuth Client ID → Web application
4. Authorized redirect URI: `https://n8n.example.com/rest/oauth2-credential/callback`
5. Kopiuj Client ID + Client Secret
6. W n8n: Credentials → New → "Google Sheets OAuth2"
   - Client ID + Secret → Connect → autoryzuj kontem Marcina

### Krok 1.5: Gmail OAuth2 (5 min, ten sam projekt Google)
1. W n8n: Credentials → New → "Gmail OAuth2"
   - Ten sam Client ID + Secret co Sheets
   - Connect → autoryzuj

### Krok 1.6: Meta (Facebook + Instagram) (30-45 min — NAJTRUDNIEJSZE)
1. https://developers.facebook.com → Create App → Business
2. App Name: "Automatyzacja Powiatu"
3. Add Products:
   - Facebook Login
   - Messenger (dla bota #4)
4. Graph API Explorer:
   - Wybierz stronę: "Powiat Kraśnicki" (lub jaką Marcin zarządza)
   - Permissions:
     ```
     pages_manage_posts
     pages_read_engagement
     pages_read_user_content
     read_insights
     pages_messaging
     instagram_basic
     instagram_content_publish
     instagram_manage_insights
     instagram_manage_comments
     ```
   - Generate Access Token → Exchange for long-lived:
     ```
     GET /oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id={APP_ID}
       &client_secret={APP_SECRET}
       &fb_exchange_token={SHORT_TOKEN}
     ```
   - Get Page Token (never-expiring):
     ```
     GET /me/accounts?access_token={LONG_LIVED_USER_TOKEN}
     ```
5. W n8n:
   - Credentials → "Query Auth" (Meta Access Token):
     - Name: `access_token`
     - Value: page token
   - Credentials → "Facebook Graph API":
     - Access Token: page token
6. Settings → Variables:
   - `FB_PAGE_ID` = ID strony z /me/accounts
   - `IG_USER_ID` = ID konta IG (z Graph API: GET /{page_id}?fields=instagram_business_account)
   - `META_PAGE_TOKEN` = page token

### Krok 1.7: SMTP lub Gmail do wysyłki (już zrobione w 1.5)
- Gmail OAuth2 wystarczy do approval flow i newslettera

### Krok 1.8: Zmienne n8n — podsumowanie
Settings → Variables:
```
FB_PAGE_ID = ...
IG_USER_ID = ...
META_PAGE_TOKEN = ...
TELEGRAM_CHAT_ID = ...
EMAIL_APPROVAL = marcin@...
EMAIL_RADNY = marcin@...
FB_VERIFY_TOKEN = marcin_bot_2026
UNSUBSCRIBE_URL = (na razie puste)
```

---

## FAZA 2 — Import i testy (2-3 godziny)

Importujemy workflow'y W KOLEJNOŚCI (zależności!):

### Krok 2.1: Google Sheets — przygotuj arkusze
Marcin tworzy JEDEN Google Sheet z arkuszami:
1. **Posty** — content calendar (kolumny: temat, tresc, ton, klient, platformy, image_url, status, email_approval)
2. **Messenger Log** — (kolumny: timestamp, sender_id, pytanie, odpowiedz, eskalacja)
3. **Kryzysy** — (kolumny: data, typ, lokalizacja, szczegoly, czas_trwania, platformy, status)
4. **Subskrybenci** — (kolumny: email, imie, data_zapisu, status)
5. **Archiwum** — newsletter archive (kolumny: numer, data, temat, wyslano_do, newsy, bip)
6. **Sentiment Log** — (kolumny: timestamp, analyzed, positive, neutral, negative, crisis, alert, alert_reason)
7. **Archiwum Postow** — (kolumny: post_id, data_publikacji, tresc, typ, link, polubienia, komentarze, udostepnienia, engagement, zalacznik_typ, zalacznik_url, data_archiwizacji)
8. **Dzienne Statystyki** — (kolumny: data, liczba_postow, laczny_engagement, sredni_engagement, top_post, top_engagement)

### Krok 2.2: Import workflow'ów — kolejność

**Dzień 1 — natychmiastowa wartość:**

| # | Import | Test | Czas |
|---|--------|------|------|
| 1 | Radar Radnego | Manual trigger → sprawdź czy RSS działa, AI generuje briefing | 15 min |
| 8 | Content Archiver | Manual trigger → sprawdź czy pobiera posty FB | 10 min |
| 3 | Raport Kliencki | Otwórz webhook URL w przeglądarce → sprawdź raport | 10 min |

**Dzień 2 — content publishing:**

| # | Import | Test | Czas |
|---|--------|------|------|
| 2 | Social Media Machine | Dodaj testowy wiersz w Sheets → sprawdź czy AI generuje 3 wersje | 20 min |
| 7 | Sentiment Monitor | Manual trigger → sprawdź czy pobiera komentarze i klasyfikuje | 15 min |

**Dzień 3 — komunikacja:**

| # | Import | Test | Czas |
|---|--------|------|------|
| 4 | Messenger FAQ Bot | Skonfiguruj webhook w Meta → wyślij testową wiadomość | 30 min |
| 5 | Crisis Rapid Publisher | Otwórz formularz → wypełnij test → sprawdź email approval | 15 min |
| 6 | Newsletter | Manual trigger → sprawdź podgląd email → wyślij test | 20 min |

**Dzień 4 — integracja:**

| # | Import | Test | Czas |
|---|--------|------|------|
| 9 | Kalkulator Wpływu | Manual trigger → sprawdź czy zbiera dane z innych arkuszy | 15 min |

### Krok 2.3: Aktywacja
Po przetestowaniu KAŻDEGO workflow'a:
1. Przełącz na Active
2. Sprawdź następnego dnia czy automatycznie odpalił

---

## FAZA 3 — Szkolenie Marcina (1 godzina)

Jedno spotkanie Zoom/Meet:

1. **Google Sheets** (15 min)
   - Jak dodać post do content calendar
   - Jak zmienić status na "do publikacji"
   - Jak sprawdzić logi

2. **Email approval** (5 min)
   - Jak wygląda email z podglądem
   - Kliknij Approve/Reject

3. **Crisis form** (5 min)
   - Bookmark URL formularza
   - Pokaz: wypełnij → approve → opublikowane

4. **Raport kliencki** (5 min)
   - Bookmark URL webhook per klient
   - Jeden klik = raport

5. **Telegram** (5 min)
   - Jak wygląda briefing rano
   - Jak wygląda alert sentymentu
   - Jak wygląda eskalacja z Messengera

6. **Co NIE wymaga uwagi** (5 min)
   - Archiver działa sam
   - Sentiment działa sam
   - Kalkulator odpala się 1-go

7. **Troubleshooting** (10 min)
   - Gdzie patrzeć gdy coś nie działa (Executions w n8n)
   - Jak ręcznie odpalić workflow
   - Kontakt do Shawna gdy problem

---

## FAZA 4 — Monitoring (ongoing)

### Pierwszy tydzień:
- Shawn sprawdza Executions codziennie
- Poprawia ewentualne błędy (BIP scraping, rate limity)

### Po tygodniu:
- Marcin działa sam
- Shawn dostępny na pytania

### Po miesiącu:
- Kalkulator Wpływu odpalił się → Marcin widzi pierwszy raport
- Ewaluacja: co działa, co poprawić

---

## Potrzebne od Marcina

- [ ] Konto Google (Gmail) — do Sheets, Gmail OAuth
- [ ] Konto Telegram — do briefingów i alertów
- [ ] Dostęp admin do strony FB Powiatu (lub której zarządza)
- [ ] Konto IG Business (podpięte pod stronę FB)
- [ ] 1-2 godziny na call konfiguracyjny
- [ ] Decyzja: gdzie hostować n8n (Mikrus / VPS / jego komputer)

## Potrzebne od Shawna

- [ ] Postawić n8n (Docker + Cloudflare Tunnel)
- [ ] Skonfigurować credentials na call'u z Marcinem
- [ ] Zaimportować i przetestować workflow'y
- [ ] Przygotować Google Sheet z arkuszami
- [ ] Szkolenie 1h
- [ ] Monitoring przez pierwszy tydzień

---

## Timeline

| Dzień | Co | Kto |
|-------|----|-----|
| 1 | Call: credentials + n8n setup | Shawn + Marcin |
| 2 | Import workflows 1, 3, 8 + testy | Shawn |
| 3 | Import workflows 2, 7 + testy | Shawn |
| 4 | Import workflows 4, 5, 6 + testy | Shawn |
| 5 | Import workflow 9 + integracja | Shawn |
| 6 | Szkolenie Marcina (1h Zoom) | Shawn + Marcin |
| 7-13 | Monitoring, poprawki | Shawn |
| 14 | Ewaluacja, handoff | Shawn + Marcin |

**Łączny czas Shawna: ~8-10 godzin**
**Łączny czas Marcina: ~3-4 godziny (2h call + 1h szkolenie + testy)**
