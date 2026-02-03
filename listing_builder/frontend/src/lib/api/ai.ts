// frontend/src/lib/api/ai.ts
// Purpose: AI optimization API calls (full, title, description, batch)
// NOT for: Product import or publishing operations

import { apiRequest } from './client'
import type {
  OptimizationRequest,
  OptimizationResponse,
  BatchOptimizationRequest,
} from '../types'

// Full product optimization (title + description)
export async function optimizeProduct(
  productId: string,
  options?: Partial<OptimizationRequest>
): Promise<OptimizationResponse> {
  const response = await apiRequest<OptimizationResponse>(
    'post',
    `/api/ai/optimize/${productId}`,
    {
      marketplace: options?.marketplace,
      target_keywords: options?.target_keywords,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Optimize title only
export async function optimizeTitle(
  productId: string,
  options?: Partial<OptimizationRequest>
): Promise<OptimizationResponse> {
  const response = await apiRequest<OptimizationResponse>(
    'post',
    `/api/ai/optimize-title/${productId}`,
    {
      marketplace: options?.marketplace,
      target_keywords: options?.target_keywords,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Optimize description only
export async function optimizeDescription(
  productId: string,
  options?: Partial<OptimizationRequest>
): Promise<OptimizationResponse> {
  const response = await apiRequest<OptimizationResponse>(
    'post',
    `/api/ai/optimize-description/${productId}`,
    {
      marketplace: options?.marketplace,
      target_keywords: options?.target_keywords,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Batch optimize multiple products
export async function batchOptimize(
  request: BatchOptimizationRequest
): Promise<{ job_id: string; total_products: number }> {
  const response = await apiRequest<{ job_id: string; total_products: number }>(
    'post',
    '/ai/batch-optimize',
    request
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
