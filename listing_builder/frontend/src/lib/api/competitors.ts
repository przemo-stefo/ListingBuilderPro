// frontend/src/lib/api/competitors.ts
// Purpose: Competitors API calls for competitor tracking data
// NOT for: Product CRUD or keyword tracking (separate files)

import type { CompetitorsResponse, GetCompetitorsParams } from '../types'

// Fetch competitors from the mock API route
// WHY: Uses Next.js API route instead of backend - will swap to real backend later
export async function getCompetitors(
  params?: GetCompetitorsParams
): Promise<CompetitorsResponse> {
  const searchParams = new URLSearchParams()

  if (params?.marketplace) {
    searchParams.set('marketplace', params.marketplace)
  }
  if (params?.search) {
    searchParams.set('search', params.search)
  }

  const query = searchParams.toString()
  const url = `/api/competitors${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch competitors')
  }

  return response.json()
}
