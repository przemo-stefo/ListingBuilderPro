// frontend/src/lib/api/listings.ts
// Purpose: Listings API calls for compliance-focused listing data
// NOT for: Product CRUD or optimization (separate files)

import type { ListingsResponse, GetListingsParams } from '../types'

// Fetch listings from the mock API route
// WHY: Uses Next.js API route instead of backend - will swap to real backend later
export async function getListings(
  params?: GetListingsParams
): Promise<ListingsResponse> {
  const searchParams = new URLSearchParams()

  if (params?.marketplace) {
    searchParams.set('marketplace', params.marketplace)
  }
  if (params?.compliance_status) {
    searchParams.set('compliance_status', params.compliance_status)
  }

  const query = searchParams.toString()
  const url = `/api/listings${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch listings')
  }

  return response.json()
}
