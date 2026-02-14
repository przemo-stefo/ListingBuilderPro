// frontend/src/lib/api/import.ts
// Purpose: Product import API calls (webhook, single, batch, job status)
// NOT for: Product CRUD or optimization operations

import { apiRequest } from './client'
import type {
  ImportJobStatus,
  SingleProductImport,
  BatchProductImport,
} from '../types'

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

// Get import job status
export async function getImportJobStatus(jobId: string): Promise<ImportJobStatus> {
  const response = await apiRequest<ImportJobStatus>(
    'get',
    `/api/import/job/${jobId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
