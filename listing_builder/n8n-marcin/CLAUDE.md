# n8n-marcin/CLAUDE.md
# Purpose: Reguły dla workflows n8n Marcina Nastarowicza na anna130
# NOT for: LBP backend/frontend, inne projekty klientów

## Klient
- **Marcin Nastarowicz** — Biuro Starosty Powiatu Kraśnickiego
- **WhatsApp JID:** 48722149435@c.us | **FB Page ID:** 100064758394256
- **WhatsApp Grupa:** `120363426348074659@g.us` ("AI Asystent") — WSZYSTKIE wiadomości idą tu
- **Kontekst:** zarządza social media powiatu, używa TYLKO WhatsApp (nie Telegram)

## Infrastruktura
- **n8n:** https://n8n-marcin.feedmasters.org (anna130, Docker)
- **Qdrant:** `qdrant:6333` (kolekcja `krasnik_news`, 768 dim Cosine)
- **WAHA:** `http://65.21.88.47:40127` (izabela166, NIE anna130!)
- **Monitoring:** healthcheck.sh co 5 min → auto-restart + Telegram alert

## Core Workflows (8 aktywne)
| ID | Nazwa | Plik | Schedule |
|----|-------|------|----------|
| 1hJYRL7dIocTYMZN | Radar Radnego v2 | 01-radar-radnego.json | codziennie 6:30 |
| yKdRPPkdrTmLWK11 | News Collector | 10-news-collector.json | co 4h |
| cQBUCuz8SkHExoNm | FB Post Generator | 11-fb-post-generator.json | webhook WhatsApp |
| UpZPGjZ4qVBa7ams | Kalendarz Sesji Rady | 12-kalendarz-sesji.json | co 12h (7:00, 19:00) |
| eioKMK3F9zmkfpQT | Auto-sugestie Postów | 13-auto-sugestie.json | codziennie 9:00 |
| BJevcP0tiQIgsPr3 | Monitor Sąsiadów | 14-monitor-sasiadow.json | poniedziałek 8:00 |
| kQLTVj1H5VxXX9ns | BIP Przetargi Monitor | 15-bip-przetargi.json | 8:00 + 14:00 |
| VEkwyF3B4IIKHEFu | Weekly Summary | 16-weekly-summary.json | piątek 17:00 |

### WhatsApp komendy (FB Post Generator)
- **Numery** (np. "1, 3") → generuj post FB z artykułów briefingu
- **"od nowa"** → przepisz ostatni post
- **"napisz post o [temat]"** → post na dowolny temat (Qdrant semantic search)
- **"skróć"** / **"wydłuż"** → zmień długość ostatniego posta
- **"stats"** / **"jak idzie?"** → podsumowanie systemu (Qdrant stats)
- **"pomoc"** → menu komend
- **Tekst** (5+ znaków) → feedback/poprawka do posta

## n8n Code Node — KRYTYCZNE ZASADY

### httpRequest (NAJWAŻNIEJSZE!)
```javascript
// DOBRZE — json:true + obiekt body
await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://qdrant:6333/collections/krasnik_news/points/scroll',
  body: { limit: 10, with_payload: true },
  json: true
});

// ŹLE — json:false + stringify = CICHO FAILUJE!
// body: JSON.stringify({...}), json: false  ← NIGDY!
```

### Sandbox — co NIE działa
- `fetch()` → użyj `this.helpers.httpRequest()`
- `require('crypto')` → użyj custom `simpleHash()` (Math.imul based)
- `require()` czegokolwiek → nie ma node_modules w sandbox

### Wzorce
- **Env vars:** `process.env.GEMINI_API_KEY` (wymaga `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`)
- **Dane z innego node'a:** `$('Node Name').first().json`
- **Qdrant payload field: `feedback`** (NIE `feedback_text` — ujednolicone 2026-02-28)
- **WAHA webhook payload:** `$json.body.payload.from` (n8n owija POST body w `$json.body`)
- **Group messages:** `payload.from` = group JID, `payload.participant` = sender JID
- **Wysyłanie:** ZAWSZE na grupę `120363426348074659@g.us` (NIE bezpośrednio do Marcina)
- **Parallel Qdrant:** `Promise.all([scroll('cat1'), scroll('cat2')])`
- **HTTP Request node auth:** `authentication: "none"` + ręczny header (nie genericCredentialType)
- **Error handling:** `"onError": "continueRegularOutput"` na RSS/HTTP/HTML nodes

## Gemini API
- **Embeddingi:** `gemini-embedding-001` + `outputDimensionality: 768` (domyślnie 3072!)
- **Generowanie:** `gemini-flash-lite-latest` (szybki, dobry output)
- **NIE DZIAŁA:** `gemini-2.0-flash`, `gemini-2.0-flash-001`, `gemini-2.0-flash-lite`

## n8n API (deploy workflows)
- API key w DB: `docker exec n8n-postgres psql -U n8n -d n8n_marcin -t -c "SELECT \"apiKey\" FROM user_api_keys LIMIT 1;"`
- Klucz się regeneruje po restarcie n8n — NIGDY nie hardcoduj!
- PUT workflow: wysyłaj TYLKO `name`, `nodes`, `connections`, `settings` (bez `tags`, `staticData`)
- Aktywacja: `POST .../api/v1/workflows/{id}/activate`

## Qdrant categories (krasnik_news)
| Kategoria | UUID | Opis |
|-----------|------|------|
| (default) | auto | Artykuły z RSS/scraping |
| briefing-index | 00000000...01 | Mapa numerów → artykuły dla FB Post Generator |
| marcin-last-post | 00000000...02 | Ostatni post FB (singleton) |
| marcin-preference | auto | Tematy które Marcin wybiera |
| marcin-style-feedback | auto | Feedback o stylu pisania |
| briefing | auto | Archiwum briefingów |
| sesja-rady-notified | auto | Sesje eSesja — notyfikowane (dedup) |
| bip-przetarg-notified | auto | Przetargi BIP — notyfikowane (dedup) |

## Deploy na anna130
```bash
# 1. Pobierz API key
KEY=$(ssh root@anna130 'docker exec n8n-postgres psql -U n8n -d n8n_marcin -t -c "SELECT \"apiKey\" FROM user_api_keys LIMIT 1;"' | tr -d ' \n')

# 2. Upload workflow
curl -X PUT "https://n8n-marcin.feedmasters.org/api/v1/workflows/{ID}" \
  -H "X-N8N-API-KEY: $KEY" -H "Content-Type: application/json" -d @file.json

# 3. Activate
curl -X POST "https://n8n-marcin.feedmasters.org/api/v1/workflows/{ID}/activate" \
  -H "X-N8N-API-KEY: $KEY"
```
