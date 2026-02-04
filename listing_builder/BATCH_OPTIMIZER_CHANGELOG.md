# Batch Optimizer — Changelog

**Data:** 2026-02-04
**Commit:** `9dfe730` — `feat: Add batch optimizer with CSV, paste, and URL import modes`
**Branch:** main (pushed)

---

## Co zostalo zbudowane

Dodano batch import do strony `/optimize` z 3 trybami importu produktow:

### 1. CSV Upload
- Upload pliku CSV z kolumnami: `product_title`, `brand`, `keywords`
- Keywords w CSV sa pipe-separated (`keyword1|keyword2|keyword3`)
- Parsowanie przez Papa Parse

### 2. Paste (wklejanie)
- Textarea — jeden produkt na linie
- Format: `title|brand|keyword1,keyword2,keyword3`
- Przycisk "Parse Products" → podglad tabeli

### 3. URLs (Allegro)
- Wklejanie linkow Allegro (jeden na linie)
- Wspolne keywords w osobnym textarea
- "Scrape & Preview" → scrape danych → podglad tabeli
- Reuse istniejacego endpointu `/converter/scrape`

### Wspolne dla batcha
- Marketplace selector (Amazon DE/US/PL, eBay DE, Kaufland)
- Mode toggle (Aggressive / Standard)
- Podglad tabeli przed optymalizacja (z mozliwoscia usuwania produktow)
- "Optimize All" → przetwarzanie sekwencyjne przez n8n
- Wyniki: rozwijane karty z coverage badge + scores + listing
- "Download All as CSV" — eksport wynikow

---

## Nowe pliki (5)

| Plik | Linie | Cel |
|------|-------|-----|
| `frontend/src/app/optimize/components/SingleTab.tsx` | ~230 | Ekstrakt formularza single-product z page.tsx |
| `frontend/src/app/optimize/components/BatchTab.tsx` | ~280 | Trzy tryby importu + podglad + optimize all |
| `frontend/src/app/optimize/components/BatchResults.tsx` | ~140 | Karty wynikow + download CSV |
| `frontend/src/app/optimize/components/ResultDisplay.tsx` | ~260 | Wspolne komponenty (ScoresCard, ListingCard, KeywordIntelCard) |
| `frontend/src/lib/utils/csvParser.ts` | ~90 | parseOptimizerCSV, parsePasteText, exportResultsCSV |

## Zmodyfikowane pliki (5)

| Plik | Zmiana |
|------|--------|
| `backend/api/optimizer_routes.py` | Dodano `POST /api/optimizer/generate-batch` — max 50 produktow, per-product error handling |
| `frontend/src/lib/types/index.ts` | Dodano BatchOptimizerRequest, BatchOptimizerResponse, ParsedBatchProduct |
| `frontend/src/lib/api/optimizer.ts` | Dodano generateBatch(), scrapeForOptimizer() |
| `frontend/src/lib/hooks/useOptimizer.ts` | Dodano useBatchOptimizer(), useScrapeForOptimizer() |
| `frontend/src/app/optimize/page.tsx` | Slim down do orchestratora z tabami Single/Batch |

## Nowa zaleznosc

- `papaparse` + `@types/papaparse` — parsowanie CSV

---

## Architektura

```
Frontend (Batch Tab)
  ↓ CSV / Paste / URLs
  ↓ parseOptimizerCSV() / parsePasteText() / scrapeForOptimizer()
  ↓ Preview table
  ↓ useBatchOptimizer() hook
  ↓ POST /api/optimizer/generate-batch
  ↓ Backend loops through products
  ↓ n8n webhook per product (sequential, 60s timeout each)
  ↓ BatchOptimizerResponse { total, succeeded, failed, results[] }
  ↓ BatchResults component (collapsible cards + CSV export)
```

**Timeout:** 300s batch, 60s per product
**Max produktow:** 50
**Error handling:** Per-product — jeden blad nie przerywa calego batcha

---

## Testowanie

1. **Single tab** — bez zmian, dziala jak wczesniej
2. **CSV upload** — upload CSV z 3 produktami → podglad → Optimize All
3. **Paste** — wklej 3 linie w formacie `title|brand|kw1,kw2` → Parse → Optimize All
4. **URLs** — wklej linki Allegro + keywords → Scrape & Preview → Optimize All
5. **Download** — po batchu kliknij "Download All as CSV"
6. **Error handling** — jeden wadliwy produkt → reszta przetwarza sie normalnie
