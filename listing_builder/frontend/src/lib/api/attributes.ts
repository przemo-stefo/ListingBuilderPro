// frontend/src/lib/api/attributes.ts
// Purpose: API client for Auto-Atrybuty endpoints
// NOT for: UI logic or state management

import { apiClient } from './client'

interface CategoryItem {
  id: string
  name: string
  path: string
  leaf: boolean
}

interface CategorySearchResponse {
  categories: CategoryItem[]
}

interface ParameterOption {
  id: string
  value: string
}

interface CategoryParameter {
  id: string
  name: string
  type: string
  required: boolean
  unit: string | null
  options: ParameterOption[]
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

export async function searchCategories(query: string): Promise<CategorySearchResponse> {
  const { data } = await apiClient.get<CategorySearchResponse>('/attributes/categories', {
    params: { query },
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
): Promise<import('../types').AttributeRunResponse> {
  // WHY: 90s timeout — LLM attribute generation takes 30-60s, default 30s causes timeouts
  const { data } = await apiClient.post<import('../types').AttributeRunResponse>('/attributes/generate', {
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
): Promise<import('../types').AttributeHistoryResponse> {
  const { data } = await apiClient.get<import('../types').AttributeHistoryResponse>('/attributes/history', {
    params: { limit, offset },
  })
  return data
}

export async function deleteAttributeHistory(id: number): Promise<void> {
  await apiClient.delete(`/attributes/history/${id}`)
}
