// frontend/src/app/products/import/constants.ts
// Purpose: Shared constants for import page (single + batch)
// NOT for: Business logic or API calls

export const MARKETPLACES = [
  { value: 'amazon', label: 'Amazon', flag: '📦' },
  { value: 'allegro', label: 'Allegro', flag: '🇵🇱' },
  { value: 'ebay', label: 'eBay', flag: '🏷️' },
  { value: 'kaufland', label: 'Kaufland', flag: '🇩🇪' },
  { value: 'bol', label: 'Bol.com', flag: '🇳🇱' },
] as const

// WHY: Allegro exports CSVs with Polish headers — we map them to our internal fields
export const COLUMN_MAP: Record<string, string> = {
  'tytuł': 'title', 'tytuł oferty': 'title', 'nazwa': 'title', 'title': 'title', 'name': 'title',
  'cena': 'price', 'price': 'price', 'cena brutto': 'price',
  'numer oferty': 'source_id', 'id oferty': 'source_id', 'offer_id': 'source_id',
  'id': 'source_id', 'asin': 'source_id', 'source_id': 'source_id', 'sku': 'source_id',
  'item number': 'source_id', 'item id': 'source_id', 'item_id': 'source_id',
  'kategoria': 'category', 'category': 'category',
  'marka': 'brand', 'brand': 'brand', 'producent': 'brand',
  'opis': 'description', 'description': 'description',
  'url': 'source_url', 'link': 'source_url', 'link do oferty': 'source_url',
  'waluta': 'currency', 'currency': 'currency',
}

export const MAX_BATCH_SIZE = 500

export interface ParsedProduct {
  title: string
  price?: number
  source_id: string
  category?: string
  brand?: string
  description?: string
  source_url?: string
  currency?: string
}
