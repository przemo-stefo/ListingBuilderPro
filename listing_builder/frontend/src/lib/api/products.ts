// frontend/src/lib/api/products.ts
// Purpose: Product-related API calls (list, get, delete, stats)
// NOT for: Import or optimization endpoints (separate files)

import { apiRequest } from './client'
import type {
  Product,
  ProductListResponse,
  ProductFilters,
  DashboardStats,
} from '../types'

// List products with filters
export async function listProducts(
  filters?: ProductFilters
): Promise<ProductListResponse> {
  const params = {
    status: filters?.status,
    marketplace: filters?.marketplace,
    source: filters?.source,
    search: filters?.search,
    min_score: filters?.min_score,
    max_score: filters?.max_score,
    sort_by: filters?.sort_by || 'created_at',
    sort_order: filters?.sort_order || 'desc',
    page: filters?.page || 1,
    page_size: filters?.page_size || 20,
  }

  const response = await apiRequest<ProductListResponse>(
    'get',
    '/products',
    undefined,
    params
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Get single product by ID
// WHY: Path must be /products/${id} not /api/products/${id} — proxy adds /api/ prefix
export async function getProduct(id: string): Promise<Product> {
  const response = await apiRequest<Product>('get', `/products/${id}`)

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Delete product
export async function deleteProduct(id: string): Promise<void> {
  const response = await apiRequest('delete', `/products/${id}`)

  if (response.error) {
    throw new Error(response.error)
  }
}

// Get dashboard stats
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiRequest<DashboardStats>(
    'get',
    '/products/stats/summary'
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
