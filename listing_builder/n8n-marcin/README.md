# Pakiet Automatyzacji Social Media + Radar Radnego
## Dla: Marcin Nastarowicz | Autor: PYROX AI

---

## Co zawiera ten pakiet?

### 1. Radar Radnego (`01-radar-radnego.json`)
Codziennie o 6:30 rano dostajesz briefing z najważniejszymi informacjami:
- **Lokalne media** — Radio Lublin, Dziennik Wschodni, NaszeMiasto Kraśnik
- **BIP Powiatu Kraśnickiego** — nowe uchwały, ogłoszenia, przetargi
- **AI podsumowanie** — 5 najważniejszych punktów + rekomendacje
- **Dostarczenie** — Telegram + email

### 2. Social Media Machine (`02-social-media-machine.json`)
Jeden wpis w Google Sheets → AI generuje posty na 3 platformy:
- **Facebook** — długi post, naturalny język, CTA
- **Instagram** — caption z hashtagami, emoji
- **X (Twitter)** — tweet max 270 znaków
- **Approval flow** — email do przełożonego → klik "OK" → autopublikacja
- **Obsługa wielu klientów** — kolumna "klient" w arkuszu

### 3. Raport Kliencki (`03-raport-kliencki.json`)
Jeden klik → profesjonalny raport:
- **Statystyki FB** — zasięg, interakcje, fani, wyświetlenia (28 dni)
- **Top 5 postów** — ranking po engagement
- **AI analiza** — podsumowanie + 3 rekomendacje na następny miesiąc
- **Piękny HTML raport** — wysłany emailem do klienta
- **Trigger** — link w przeglądarce: `/webhook/raport?client=powiat`

---

## Szybki Start

### Krok 1: Zainstaluj n8n
```bash
# Docker (najłatwiej)
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n

# Otwórz: http://localhost:5678
```

### Krok 2: Utwórz konta (darmowe)

| Usługa | URL | Do czego |
|--------|-----|----------|
| **Groq** | console.groq.com | AI dla Radar Radnego — DARMOWY! |
| **Gemini** | aistudio.google.com | AI dla Social Media (Flash 2.0) — DARMOWY! |
| **Telegram Bot** | @BotFather na Telegram | Dostarczanie briefingów |
| **Meta Developer** | developers.facebook.com | Publikowanie na FB + IG |
| **Google Cloud** | console.cloud.google.com | Google Sheets API |

### Krok 3: Skonfiguruj credentials w n8n

**Groq API Key (Radar Radnego):**
1. Wejdź na console.groq.com → API Keys → Create
2. W n8n: Settings → Credentials → New → "Header Auth"
3. Name: `Authorization`, Value: `Bearer sk-twój-klucz`

**Gemini API Key (Social Media Machine):**
1. Wejdź na aistudio.google.com → Get API Key → Create
2. W n8n: Settings → Credentials → New → "Query Auth"
3. Name: `key`, Value: `AIza-twój-klucz`

**Telegram Bot:**
1. Otwórz @BotFather → /newbot → skopiuj token
2. Napisz do bota, potem otwórz: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Skopiuj `chat_id` z odpowiedzi
4. W n8n: Credentials → Telegram API → wklej token

**Meta (Facebook + Instagram):**
1. developers.facebook.com → Create App → Business
2. Dodaj "Facebook Login" + "Pages API" + "Instagram API"
3. Graph API Explorer → wygeneruj Page Access Token z permissions:
   - `pages_manage_posts`, `pages_read_engagement`, `read_insights`
   - `instagram_content_publish`, `instagram_basic`, `instagram_manage_insights`
4. Wymień na long-lived token (instrukcja w sticky notes workflow'u)

**Google Sheets:**
1. console.cloud.google.com → APIs → włącz Google Sheets API
2. Credentials → OAuth 2.0 Client → skopiuj Client ID + Secret
3. W n8n: Credentials → Google Sheets OAuth2

### Krok 4: Importuj workflow'y
1. Otwórz n8n → Workflows → Import
2. Wczytaj każdy plik JSON
3. Otwórz workflow → skonfiguruj nodes oznaczone "CONFIGURE_ME"
4. Ustaw Variables w Settings:
   - `TELEGRAM_CHAT_ID` — Twój chat ID
   - `EMAIL_RADNY` — Twój email
   - `FB_PAGE_ID` — ID strony Facebook
   - `IG_USER_ID` — ID konta Instagram Business
   - `META_PAGE_TOKEN` — Long-lived Page Token
   - `EMAIL_APPROVAL` — Email osoby zatwierdzającej posty

### Krok 5: Aktywuj!
1. Każdy workflow → przełącz na "Active"
2. Radar Radnego odpali się następnego dnia o 6:30
3. Social Media Machine czeka na nowe wiersze w arkuszu
4. Raport — otwórz link webhook w przeglądarce

---

## Google Sheets — Szablon Content Calendar

Utwórz arkusz o nazwie **"Posty"** z kolumnami:

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| **temat** | **tresc** | **ton** | **klient** | **platformy** | **image_url** | **status** | **email_approval** |
| Dni Miasta | Zapraszamy na Dni Kraśnika 15-17.06! | luźny | Powiat Kraśnicki | fb,ig,x | https://... | do publikacji | szef@example.com |

**Status:**
- `do publikacji` → uruchamia workflow
- `Opublikowano ✅` → auto-wypełniane po publikacji

---

## Źródła danych Radar Radnego

| Źródło | Typ | URL |
|--------|-----|-----|
| Radio Lublin | RSS | `https://radio.lublin.pl/feed/` |
| Dziennik Wschodni | RSS | `https://www.dziennikwschodni.pl/rss/articles/pl` |
| NaszeMiasto Kraśnik | RSS | `https://krasnik.naszemiasto.pl/rss/artykuly/1.xml` |
| BIP Ogłoszenia | HTML scraping | `https://powiatkrasnik.e-bip.eu/index.php?id=722` |
| BIP Uchwały Rady | HTML scraping | `https://powiatkrasnik.e-bip.eu/index.php?id=857` |

---

## Koszty

| Usługa | Koszt |
|--------|-------|
| n8n (self-hosted) | **0 zł** |
| Groq AI (Radar Radnego) | **0 zł** (darmowy tier) |
| Gemini Flash 2.0 (Social Media) | **0 zł** (darmowy tier, 1500 req/dzień) |
| Telegram Bot | **0 zł** |
| Meta Graph API | **0 zł** |
| Google Sheets API | **0 zł** |
| **RAZEM** | **0 zł/mies** |

---

## 4. Messenger FAQ Bot (`04-messenger-faq-bot.json`)

Automatyczny chatbot na Messengerze strony FB Powiatu:
- **Baza wiedzy** — godziny, telefony, adresy WSZYSTKICH wydziałów (Komunikacja, Geodezja, Budownictwo, PUP, PCPR...)
- **AI (Gemini Flash)** — rozumie pytania i odpowiada naturalnie, po polsku
- **Eskalacja** — jeśli AI nie zna odpowiedzi → alert na Telegram do Marcina
- **RODO log** — wszystkie rozmowy logowane w Google Sheets (retencja 30 dni)
- **Rozróżnia kompetencje** — wie co robi starostwo, a co gmina (śmieci, meldunki → "proszę do gminy")

**Setup Facebook Messenger Platform:**
1. developers.facebook.com → Your App → Add Product → Messenger
2. Webhooks → Callback URL: `https://twoj-n8n/webhook/messenger-bot`
3. Verify Token: `marcin_bot_2026`
4. Subscribe to: `messages`
5. Generate Page Token

---

## 5. Crisis Rapid Publisher (`05-crisis-rapid-publisher.json`)

Szybka publikacja w sytuacjach kryzysowych:
- **Formularz n8n** — otwierasz URL, wypełniasz 5 pól, gotowe
- **11 typów kryzysów** — awaria wody/prądu, zamknięcie drogi, powódź, pogoda, pożar, zmiana godzin...
- **AI (Gemini Flash)** — generuje 3 wersje (FB/IG/X) w tonie spokojnym, rzeczowym, bez paniki
- **Dual approval** — email + Telegram alert jednocześnie
- **Jednym klikiem** — publikacja na wybranych platformach (FB / FB+IG / wszystkie)
- **Log kryzysów** — archiwum w Google Sheets
- **Z 30 minut → 2-3 minuty**

---

## 6. Newsletter "Głos Powiatu" (`06-newsletter-glos-powiatu.json`)

Tygodniowy newsletter dla mieszkańców:
- **Co piątek o 9:00** — zbiera newsy z RSS + BIP (ostatnie 7 dni)
- **Filtruje** po Kraśniku i 10 gminach powiatu
- **Gemini Flash** pisze newsletter: powitanie, top 5 wydarzeń, BIP ludzkim językiem, "co nas czeka", słowo od radnego
- **Piękny HTML template** — gradient header, footer z danymi kontaktowymi starostwa
- **Approval flow** — podgląd emailem → Approve → wysyłka
- **Lista subskrybentów** w Google Sheets + endpoint zapisu (`POST /webhook/newsletter-subscribe`)
- **Archiwum** — każdy numer logowany z datą i statystykami
- **Wartość polityczna** — lista mailingowa niezależna od algorytmów FB

---

## 7. Sentiment Monitor (`07-sentiment-monitor.json`)

Monitoring nastrojów w komentarzach na FB Powiatu:
- **Co 15 minut** — pobiera posty (24h) + komentarze
- **Gemini Flash** (temp 0.1) klasyfikuje KAŻDY komentarz: sentiment (POSITIVE/NEUTRAL/NEGATIVE/CRISIS), temat, priorytet
- **Alert na Telegram** gdy: CRISIS/URGENT lub 3+ negatywnych naraz
- **Log sentymentu** w Google Sheets (do wykresów trendów)

## 8. Content Archiver (`08-content-archiver.json`)

Automatyczna archiwizacja postów FB (wymóg prawny):
- **Codziennie o 23:30** — pobiera posty z ostatnich 24h
- Archiwizuje: treść, link, typ, załączniki, polubienia, komentarze, udostępnienia
- **Dzienne statystyki** — liczba postów, engagement, top post dnia
- 2 arkusze: "Archiwum Postow" + "Dzienne Statystyki"

## 9. Kalkulator Wpływu (`09-kalkulator-wplywu.json`)

"Co zrobiłem dla powiatu" — miesięczne podsumowanie:
- **1-go dnia miesiąca o 8:00** — zbiera dane ze WSZYSTKICH workflow'ów
- Źródła: FB Insights + Messenger Log + Archiwum Postów + Log Kryzysów
- **Metryki:** zasięg, posty, wiadomości, auto-obsługa %, kryzysy, zaoszczędzony czas
- **Gemini Flash** generuje post na FB z twardymi danymi
- **Email z dashboardem** (grid 6 metryk) + approval → publikacja na FB
- **Wartość wyborcza:** twarde liczby zamiast pustych obietnic

---

## Rozbudowa (Faza 4 — przyszłość)

- **Event Calendar Pipeline** — Google Calendar → automatyczne posty o wydarzeniach

---

## Kontakt

**PYROX AI, LLC** | shawnstefaniak@pyroxai.com
Workflow'y zbudowane z myślą o polskich samorządach.
