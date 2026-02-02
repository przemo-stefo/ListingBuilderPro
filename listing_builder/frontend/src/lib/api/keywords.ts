// frontend/src/lib/api/keywords.ts
// Purpose: Keywords API calls for SEO keyword tracking data
// NOT for: Product CRUD or optimization (separate files)

import type { KeywordsResponse, GetKeywordsParams } from '../types'

// Fetch keywords from the mock API route
// WHY: Uses Next.js API route instead of backend - will swap to real backend later
export async function getKeywords(
  params?: GetKeywordsParams
): Promise<KeywordsResponse> {
  const searchParams = new URLSearchParams()

  if (params?.marketplace) {
    searchParams.set('marketplace', params.marketplace)
  }
  if (params?.search) {
    searchParams.set('search', params.search)
  }

  const query = searchParams.toString()
  const url = `/api/keywords${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch keywords')
  }

  return response.json()
}
