// frontend/src/lib/api/analytics.ts
// Purpose: Analytics API calls for sales performance and revenue data
// NOT for: Product CRUD or inventory tracking (separate files)

import type { AnalyticsResponse, GetAnalyticsParams } from '../types'

// Fetch analytics from the mock API route
// WHY: Uses Next.js API route instead of backend - will swap to real backend later
export async function getAnalytics(
  params?: GetAnalyticsParams
): Promise<AnalyticsResponse> {
  const searchParams = new URLSearchParams()

  if (params?.marketplace) {
    searchParams.set('marketplace', params.marketplace)
  }
  if (params?.period) {
    searchParams.set('period', params.period)
  }

  const query = searchParams.toString()
  const url = `/api/analytics${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch analytics')
  }

  return response.json()
}
