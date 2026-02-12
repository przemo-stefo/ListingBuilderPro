// frontend/src/lib/api/analytics.ts
// Purpose: Analytics API calls for sales performance and revenue data
// NOT for: Product CRUD or inventory tracking (separate files)

import { apiRequest } from './client'
import type { AnalyticsResponse, GetAnalyticsParams } from '../types'

// Fetch analytics from backend API
export async function getAnalytics(
  params?: GetAnalyticsParams
): Promise<AnalyticsResponse> {
  const response = await apiRequest<AnalyticsResponse>(
    'get',
    '/analytics',
    undefined,
    {
      marketplace: params?.marketplace,
      period: params?.period,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
