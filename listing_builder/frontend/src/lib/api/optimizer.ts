// frontend/src/lib/api/optimizer.ts
// Purpose: API calls for the n8n Listing Optimizer workflow
// NOT for: React hooks or UI logic (those are in hooks/useOptimizer.ts)

import { apiRequest } from './client'
import type {
  OptimizerRequest,
  OptimizerResponse,
  BatchOptimizerRequest,
  BatchOptimizerResponse,
  ScrapeResponse,
} from '../types'

// WHY: n8n runs 3 sequential LLM calls — can take 10-20s total
const OPTIMIZER_TIMEOUT = 60_000

export async function generateListing(
  payload: OptimizerRequest
): Promise<OptimizerResponse> {
  const response = await apiRequest<OptimizerResponse>(
    'post',
    '/optimizer/generate',
    payload
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// WHY: Batch can take 5s per product × up to 50 products
export async function generateBatch(
  payload: BatchOptimizerRequest
): Promise<BatchOptimizerResponse> {
  const response = await apiRequest<BatchOptimizerResponse>(
    'post',
    '/optimizer/generate-batch',
    payload
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// WHY: Reuse existing scrape endpoint to pull product data from Allegro URLs
export async function scrapeForOptimizer(
  urls: string[]
): Promise<ScrapeResponse> {
  const response = await apiRequest<ScrapeResponse>(
    'post',
    '/converter/scrape',
    { urls, delay: 2.0 }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

export async function checkOptimizerHealth(): Promise<{
  status: string
  n8n_status?: number
  webhook_url?: string
  error?: string
}> {
  const response = await apiRequest<{
    status: string
    n8n_status?: number
    webhook_url?: string
    error?: string
  }>('get', '/optimizer/health')

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
