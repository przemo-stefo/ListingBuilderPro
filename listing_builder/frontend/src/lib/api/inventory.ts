// frontend/src/lib/api/inventory.ts
// Purpose: Inventory API calls for stock level tracking data
// NOT for: Product CRUD or competitor tracking (separate files)

import type { InventoryResponse, GetInventoryParams } from '../types'

// Fetch inventory from the mock API route
// WHY: Uses Next.js API route instead of backend - will swap to real backend later
export async function getInventory(
  params?: GetInventoryParams
): Promise<InventoryResponse> {
  const searchParams = new URLSearchParams()

  if (params?.marketplace) {
    searchParams.set('marketplace', params.marketplace)
  }
  if (params?.status) {
    searchParams.set('status', params.status)
  }
  if (params?.search) {
    searchParams.set('search', params.search)
  }

  const query = searchParams.toString()
  const url = `/api/inventory${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch inventory')
  }

  return response.json()
}
