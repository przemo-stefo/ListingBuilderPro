// frontend/src/lib/api/inventory.ts
// Purpose: Inventory API calls for stock level tracking data
// NOT for: Product CRUD or competitor tracking (separate files)

import { apiRequest } from './client'
import type { InventoryResponse, GetInventoryParams } from '../types'

// Fetch inventory from backend API
export async function getInventory(
  params?: GetInventoryParams
): Promise<InventoryResponse> {
  const response = await apiRequest<InventoryResponse>(
    'get',
    '/inventory',
    undefined,
    {
      marketplace: params?.marketplace,
      status: params?.status,
      search: params?.search,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
