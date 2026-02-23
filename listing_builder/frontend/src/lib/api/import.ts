// frontend/src/lib/api/import.ts
// Purpose: Product import API calls (webhook, single, batch, job status)
// NOT for: Product CRUD or optimization operations

import { apiRequest } from './client'
import type {
  ImportJobStatus,
  SingleProductImport,
  BatchProductImport,
} from '../types'

// WHY: Scraped product shape matches backend AllegroProduct dataclass
export interface ScrapedProduct {
  title: string
  price: number | null
  currency: string
  source_id: string
  source_url: string
  brand: string
  category: string
  description: string
  ean: string
  images: string[]
  parameters: Record<string, string>
  bullet_points: string[]
}

// Scrape product data from marketplace URL (returns data, does NOT import)
export async function scrapeProductUrl(
  url: string,
  marketplace?: string
): Promise<ScrapedProduct> {
  const response = await apiRequest<{ product: ScrapedProduct }>(
    'post',
    '/import/scrape-url',
    { url, marketplace }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!.product
}

// Import from n8n webhook
export async function importFromWebhook(data: Record<string, unknown>): Promise<ImportJobStatus> {
  const response = await apiRequest<ImportJobStatus>(
    'post',
    '/import/webhook',
    data
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Import single product
export async function importSingleProduct(
  product: SingleProductImport
): Promise<{ product_id: string }> {
  const response = await apiRequest<{ product_id: string }>(
    'post',
    '/import/product',
    product
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Import batch of products
// WHY: Backend expects List[ProductImport] as body + source as query param (not wrapped in object)
export async function importBatchProducts(
  products: SingleProductImport[],
  source: string = 'allegro'
): Promise<ImportJobStatus> {
  const response = await apiRequest<ImportJobStatus>(
    'post',
    `/import/batch?source=${source}`,
    products
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Import from connected Allegro account by offer IDs
export async function importFromAllegro(
  offerIds: string[]
): Promise<{ success_count: number; failed_count: number; errors: string[] }> {
  const response = await apiRequest<{ success_count: number; failed_count: number; errors: string[] }>(
    'post',
    '/import/from-allegro',
    { offer_ids: offerIds }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Get import job status
// WHY: Path without /api/ prefix — the proxy route.ts adds /api/ automatically
export async function getImportJobStatus(jobId: string): Promise<ImportJobStatus> {
  const response = await apiRequest<ImportJobStatus>(
    'get',
    `/import/job/${jobId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
