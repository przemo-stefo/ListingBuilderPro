// frontend/src/lib/api/optimizer.ts
// Purpose: API calls for the n8n Listing Optimizer workflow
// NOT for: React hooks or UI logic (those are in hooks/useOptimizer.ts)

import { apiClient, apiRequest } from './client'
import type {
  OptimizerRequest,
  OptimizerResponse,
  BatchOptimizerRequest,
  BatchOptimizerResponse,
  ScrapeResponse,
  ApiError,
} from '../types'

// WHY: Custom error preserves HTTP status code from backend
class OptimizerError extends Error {
  code: string
  constructor(message: string, code: string) {
    super(message)
    this.code = code
    this.name = 'OptimizerError'
  }
}

// WHY: Shared helper — throws OptimizerError with HTTP code for hook differentiation
function throwApiError(error: unknown): never {
  const apiErr = error as ApiError
  throw new OptimizerError(
    apiErr.message || 'Nieoczekiwany błąd',
    apiErr.code || '500',
  )
}

export async function generateListing(
  payload: OptimizerRequest
): Promise<OptimizerResponse> {
  try {
    const { data } = await apiClient.post<OptimizerResponse>('/optimizer/generate', payload)
    return data
  } catch (error) {
    throwApiError(error)
  }
}

// WHY: Batch can take 5s per product × up to 50 products
export async function generateBatch(
  payload: BatchOptimizerRequest
): Promise<BatchOptimizerResponse> {
  try {
    const { data } = await apiClient.post<BatchOptimizerResponse>('/optimizer/generate-batch', payload)
    return data
  } catch (error) {
    throwApiError(error)
  }
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
