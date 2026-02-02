// frontend/src/lib/api/listings.ts
// Purpose: Listings API calls for compliance-focused listing data
// NOT for: Product CRUD or optimization (separate files)

import { apiRequest } from './client'
import type { ListingsResponse, GetListingsParams } from '../types'

// Fetch listings from backend API
export async function getListings(
  params?: GetListingsParams
): Promise<ListingsResponse> {
  const response = await apiRequest<ListingsResponse>(
    'get',
    '/api/listings',
    undefined,
    {
      marketplace: params?.marketplace,
      compliance_status: params?.compliance_status,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
