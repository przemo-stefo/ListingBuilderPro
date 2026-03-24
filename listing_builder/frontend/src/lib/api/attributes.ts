// frontend/src/lib/api/attributes.ts
// Purpose: API client for Auto-Atrybuty endpoints
// NOT for: UI logic or state management

import { apiClient } from './client'
import type { AllegroCategory, CategoryParameter, AttributeRunResponse, AttributeHistoryResponse } from '../types'

interface CategorySearchResponse {
  categories: AllegroCategory[]
}

interface CategoryParametersResponse {
  parameters: CategoryParameter[]
  category_id: string
}

interface ResolveUrlResponse {
  title: string
  category_id: string
  category_name: string
  category_path: string
  leaf: boolean
}

export async function resolveAllegroUrl(url: string): Promise<ResolveUrlResponse> {
  const { data } = await apiClient.get<ResolveUrlResponse>('/attributes/resolve-url', {
    params: { url },
  })
  return data
}

export async function searchCategories(query: string, signal?: AbortSignal): Promise<CategorySearchResponse> {
  const { data } = await apiClient.get<CategorySearchResponse>('/attributes/categories', {
    params: { query },
    signal,
  })
  return data
}

export async function getCategoryParameters(categoryId: string): Promise<CategoryParametersResponse> {
  const { data } = await apiClient.get<CategoryParametersResponse>(`/attributes/categories/${categoryId}/parameters`)
  return data
}

export async function generateAttributes(
  productInput: string,
  categoryId: string,
  categoryName: string,
  categoryPath: string,
  marketplace: 'allegro' | 'kaufland' = 'allegro',
): Promise<AttributeRunResponse> {
  // WHY: 90s timeout — LLM attribute generation takes 30-60s, default 30s causes timeouts
  const { data } = await apiClient.post<AttributeRunResponse>('/attributes/generate', {
    product_input: productInput,
    category_id: categoryId,
    category_name: categoryName,
    category_path: categoryPath,
    marketplace,
  }, { timeout: 90000 })
  return data
}

export async function getAttributeHistory(
  limit: number = 20,
  offset: number = 0,
): Promise<AttributeHistoryResponse> {
  const { data } = await apiClient.get<AttributeHistoryResponse>('/attributes/history', {
    params: { limit, offset },
  })
  return data
}

export async function deleteAttributeHistory(id: number): Promise<void> {
  await apiClient.delete(`/attributes/history/${id}`)
}
