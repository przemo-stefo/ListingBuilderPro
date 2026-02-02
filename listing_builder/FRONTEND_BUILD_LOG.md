# Listing Builder Pro — Frontend Build Log

**Projekt:** ListingBuilderPro / Marketplace Listing Automation System
**Data:** 2026-02-02
**Stack:** Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui + React Query
**Repo:** https://github.com/przemo-stefo/ListingBuilderPro.git
**Branch:** main

---

## Statystyki

| Metryka | Wartość |
|---------|--------|
| Pliki TypeScript/TSX | 47 |
| Łączne linie kodu | 6,284 |
| Strony (pages) | 12 |
| Mock API routes | 6 |
| React Query hooks | 8 |
| API client functions | 11 plików |
| Commity | 27 |

---

## Architektura — 4-warstwowy pattern

Każda funkcjonalność zbudowana w tym samym wzorcu:

```
Types (lib/types/index.ts)
  → Mock API Route (app/api/*/route.ts)
    → API Client Function (lib/api/*.ts)
      → React Query Hook (lib/hooks/*.ts)
        → Page Component (app/*/page.tsx)
```

---

## Zbudowane strony (12/12 — KOMPLET)

### 1. Dashboard (`/`)
- **Plik:** `frontend/src/app/page.tsx` (171 linii)
- **Opis:** Przegląd statystyk — łączne produkty, pending, optimized, published, failed, avg score
- **Hook:** `useDashboardStats`
- **Commit:** `26b9745` fix: Add mock API routes so dashboard works without external backend

### 2. Products (`/products`)
- **Plik:** `frontend/src/app/products/page.tsx` (209 linii)
- **Opis:** Lista produktów z filtrami (status, marketplace, search), sortowaniem, paginacją
- **Hook:** `useProducts`, `useDeleteProduct`
- **API:** `listProducts`, `deleteProduct`
- **Commit:** `a2da382` feat: ListingBuilderPro with Helium 10 light theme

### 3. Product Detail (`/products/[id]`)
- **Plik:** `frontend/src/app/products/[id]/page.tsx` (207 linii)
- **Opis:** Szczegóły produktu — tytuł, opis, bullet points, cena, SEO keywords, score
- **Hook:** `useProduct`
- **API:** `getProduct`

### 4. Import (`/products/import`)
- **Plik:** `frontend/src/app/products/import/page.tsx` (308 linii)
- **Opis:** Formularz importu — single product (ASIN/tytuł/opis/bullets) + batch JSON
- **API:** `importSingleProduct`, `importBatchProducts`

### 5. Listings (`/listings`)
- **Plik:** `frontend/src/app/listings/page.tsx` (270 linii)
- **Opis:** Compliance-focused — filtry marketplace/status, badges (compliant/warning/suppressed/blocked), summary cards
- **Hook:** `useListings`
- **Mock API:** `app/api/listings/route.ts` (10 fixtures)
- **Commit:** `a43865d` feat: Add compliance-focused listings page

### 6. Keywords (`/keywords`)
- **Plik:** `frontend/src/app/keywords/page.tsx` (303 linie)
- **Opis:** SEO tracking — search volume, current rank, trend (up/down/stable), relevance score
- **Hook:** `useKeywords`
- **Mock API:** `app/api/keywords/route.ts` (15 fixtures)
- **Commit:** `6917c3c` feat: Add keywords page with SEO tracking

### 7. Competitors (`/competitors`)
- **Plik:** `frontend/src/app/competitors/page.tsx` (346 linii)
- **Opis:** Porównanie cen i ratingów — their price vs our price, status (winning/losing/tied), reviews
- **Hook:** `useCompetitors`
- **Mock API:** `app/api/competitors/route.ts` (15 fixtures)
- **Commit:** `87ada94` feat: Add competitors page with pricing comparison

### 8. Inventory (`/inventory`)
- **Plik:** `frontend/src/app/inventory/page.tsx` (382 linie)
- **Opis:** Stock levels — quantity, reorder point, days of supply, status (in_stock/low/out/overstock), total value
- **Hook:** `useInventory`
- **Mock API:** `app/api/inventory/route.ts` (randomized)
- **Commit:** `9f98af0` feat: Add inventory page with stock level tracking

### 9. Analytics (`/analytics`)
- **Plik:** `frontend/src/app/analytics/page.tsx` (366 linii)
- **Opis:** Revenue charts — total revenue/orders/conversion/AOV, revenue by marketplace (horizontal bars), monthly trend (vertical bars), top products table
- **Hook:** `useAnalytics`
- **Mock API:** `app/api/analytics/route.ts` (randomized)
- **Commit:** `e60084f` feat: Add analytics page with revenue charts

### 10. Optimize (`/optimize`)
- **Plik:** `frontend/src/app/optimize/page.tsx` (202 linie)
- **Opis:** AI optimization — wybór produktów checkbox, target keywords, batch optimize
- **Hook:** `useProducts`
- **API:** `batchOptimize`

### 11. Publish (`/publish`)
- **Plik:** `frontend/src/app/publish/page.tsx` (275 linii)
- **Opis:** Publikacja na marketplace — wybór produktów, marketplace select, bulk publish
- **Hook:** `useProducts`
- **API:** `bulkPublish`, `listMarketplaces`

### 12. Settings (`/settings`)
- **Plik:** `frontend/src/app/settings/page.tsx` (402 linie)
- **Opis:** 4 sekcje konfiguracji:
  - **General** — store name, default marketplace, timezone
  - **Marketplace Connections** — 5 marketplace'ów (Amazon/eBay/Walmart/Shopify/Allegro), connect/disconnect, API key
  - **Notifications** — 4 toggles (email, low stock, competitor price, compliance)
  - **Data & Export** — format (CSV/JSON/Excel), sync frequency (manual/1h/6h/12h/24h)
- **Hook:** `useSettings`, `useUpdateSettings`
- **Mock API:** `app/api/settings/route.ts` (mutable state, GET + PUT)
- **Commit:** `533e5cd` feat: Add settings page with general, marketplace, notification, and export config

---

## Mock API Routes (6)

| Endpoint | Method | Fixtures | Plik |
|----------|--------|----------|------|
| `/api/listings` | GET | 10 | `app/api/listings/route.ts` |
| `/api/keywords` | GET | 15 | `app/api/keywords/route.ts` |
| `/api/competitors` | GET | 15 | `app/api/competitors/route.ts` |
| `/api/inventory` | GET | randomized | `app/api/inventory/route.ts` |
| `/api/analytics` | GET | randomized | `app/api/analytics/route.ts` |
| `/api/settings` | GET, PUT | mutable state | `app/api/settings/route.ts` |

---

## React Query Hooks (8)

| Hook | Plik | Typ |
|------|------|-----|
| `useProducts` | `hooks/useProducts.ts` | Query + filter params |
| `useProduct` | `hooks/useProducts.ts` | Query by ID |
| `useDeleteProduct` | `hooks/useProducts.ts` | Mutation + toast |
| `useDashboardStats` | `hooks/useProducts.ts` | Query |
| `useListings` | `hooks/useListings.ts` | Query + filter params |
| `useKeywords` | `hooks/useKeywords.ts` | Query + filter params |
| `useCompetitors` | `hooks/useCompetitors.ts` | Query + filter params |
| `useInventory` | `hooks/useInventory.ts` | Query + filter params |
| `useAnalytics` | `hooks/useAnalytics.ts` | Query + filter params |
| `useSettings` | `hooks/useSettings.ts` | Query |
| `useUpdateSettings` | `hooks/useSettings.ts` | Mutation + toast |
| `useToast` | `hooks/useToast.ts` | Custom state |

---

## API Client Functions (11 plików)

| Plik | Funkcje |
|------|---------|
| `client.ts` | `apiClient` (axios), `apiRequest` (generic wrapper) |
| `products.ts` | `listProducts`, `getProduct`, `deleteProduct`, `getDashboardStats` |
| `listings.ts` | `getListings` |
| `keywords.ts` | `getKeywords` |
| `competitors.ts` | `getCompetitors` |
| `inventory.ts` | `getInventory` |
| `analytics.ts` | `getAnalytics` |
| `ai.ts` | `optimizeProduct`, `batchOptimize` |
| `import.ts` | `importSingleProduct`, `importBatchProducts` |
| `export.ts` | `listMarketplaces`, `bulkPublish`, `getExports` |
| `settings.ts` | `getSettings`, `updateSettings` |

---

## TypeScript Types (`lib/types/index.ts`)

- `Product`, `ProductListResponse`, `ProductFilters`
- `ImportJobStatus`, `SingleProductImport`, `BatchProductImport`
- `OptimizationRequest`, `OptimizationResponse`, `BatchOptimizationRequest`
- `PublishRequest`, `PublishResponse`, `BulkPublishRequest`, `BulkPublishResponse`
- `Marketplace`, `DashboardStats`
- `ComplianceStatus`, `ListingItem`, `ListingsResponse`, `GetListingsParams`
- `KeywordTrend`, `KeywordItem`, `KeywordsResponse`, `GetKeywordsParams`
- `CompetitorStatus`, `CompetitorItem`, `CompetitorsResponse`, `GetCompetitorsParams`
- `StockStatus`, `InventoryItem`, `InventoryResponse`, `GetInventoryParams`
- `MarketplaceRevenue`, `MonthlyRevenue`, `TopProduct`, `AnalyticsResponse`, `GetAnalyticsParams`
- `MarketplaceId`, `MarketplaceConnection`, `NotificationSettings`, `ExportFormat`, `SyncFrequency`
- `GeneralSettings`, `DataExportSettings`, `SettingsResponse`, `UpdateSettingsPayload`
- `ApiResponse<T>`, `ApiError`

---

## UI Components (shadcn/ui)

| Komponent | Plik |
|-----------|------|
| Button | `components/ui/button.tsx` — 5 wariantów (default/destructive/outline/secondary/ghost) |
| Card | `components/ui/card.tsx` — Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter |
| Input | `components/ui/input.tsx` — dark mode styling |
| Badge | `components/ui/badge.tsx` — z ComplianceBadge helper |
| Toaster | `components/ui/toaster.tsx` — toast notifications |

---

## Layout & Navigation

- **Sidebar:** `components/layout/Sidebar.tsx` — 11 nav items, dark mode (#121212), active state (white bg)
- **Layout:** `app/layout.tsx` — flex (sidebar + main), React Query provider, Toaster
- **QueryProvider:** `components/providers/QueryProvider.tsx` — QueryClient z 60s staleTime, retry 1

---

## Design System

| Element | Wartość |
|---------|--------|
| Primary BG | `#1A1A1A` |
| Secondary BG | `#121212` |
| Card borders | `border-gray-800` |
| Text primary | `text-white` |
| Text secondary | `text-gray-400` |
| Active nav | `bg-white text-black` |
| Connected badge | `bg-green-500/20 text-green-400` |
| Disconnected badge | `bg-gray-700 text-gray-400` |

---

## Historia commitów (chronologicznie)

```
a2da382 feat: ListingBuilderPro with Helium 10 light theme
5ab0612 docs: Add README with project documentation
dba6670 feat: Add Review Analyzer Pro with advanced sentiment analysis
50df308 fix(security): Add XSS protection for review analyzer
23ab137 feat: Update frontend for Review Analyzer v3 features
f26c007 fix: Update webhook URL to use HTTPS tunnel endpoint
f5445e7 fix: Update API endpoints for Listing Generator and Review Analyzer
cafccaa feat: Add description, features and FAQ sections to landing page
db02d0f feat: Add YouTube transcript server for viral content analysis
5fe24a6 feat: Add AI-powered viral pattern learning system with Qdrant
b0c74b4 feat: Add Oh My Cake landing page - complete bakery website
a3b4e69 feat: Add Compliance Guard landing page matching Lovable reference
9567d52 feat: Add promotional mockup screenshots for Compliance Guard landing page
9452037 feat: Switch landing page navbar strings to English
26b9745 fix: Add mock API routes so dashboard works without external backend
823fe90 feat: Add alerts page with filtering and fix sidebar navigation
d72e063 feat: Add inventory page with mock API and filtering
a28c5d1 feat: Add buy box page with mock API and lost-only filter
aa59ce5 feat: Add metrics page with mock API and marketplace filter
931d807 feat: Add settings page with connections, notifications, and API config
ed13d75 feat: Add login page and route navbar Sign In through it
a43865d feat: Add compliance-focused listings page with filters and summary cards
6917c3c feat: Add keywords page with SEO tracking, filters, and summary cards
87ada94 feat: Add competitors page with pricing comparison, ratings, and status tracking
9f98af0 feat: Add inventory page with stock level tracking, filters, and supply metrics
e60084f feat: Add analytics page with revenue charts, marketplace breakdown, and top products
533e5cd feat: Add settings page with general, marketplace, notification, and export config
```

---

## Co brakuje (do produkcji)

### Priorytet 1 — Krytyczne
- [ ] Podłączenie mock routes do prawdziwego backendu (`localhost:8000`)
- [ ] Prawdziwe CRUD operacje na produktach
- [ ] Integracja z marketplace API (Amazon SP-API, eBay, itp.)

### Priorytet 2 — Ważne
- [ ] Edycja szczegółów produktu (formularz)
- [ ] Upload CSV/Excel do importu
- [ ] Prawdziwe przechowywanie credentials z Settings
- [ ] System notyfikacji email

### Priorytet 3 — Średnie
- [ ] Prawdziwy compliance checking
- [ ] Prawdziwy competitor tracking (scraping/API)
- [ ] Prawdziwy keyword ranking (SEO tools)
- [ ] Export danych do CSV/JSON/Excel (generacja plików)

---

## Jak uruchomić

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

Build produkcyjny:
```bash
npm run build   # zero errors
npm start       # production mode
```
