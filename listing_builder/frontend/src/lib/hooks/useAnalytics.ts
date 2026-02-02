// frontend/src/lib/hooks/useAnalytics.ts
// Purpose: React Query hook for analytics and revenue data fetching
// NOT for: Direct API calls (those are in lib/api/analytics.ts)

import { useQuery } from '@tanstack/react-query'
import { getAnalytics } from '../api/analytics'
import type { GetAnalyticsParams } from '../types'

// WHY: Same pattern as useInventory - React Query handles caching and refetching
export function useAnalytics(params?: GetAnalyticsParams) {
  return useQuery({
    queryKey: ['analytics', params],
    queryFn: () => getAnalytics(params),
    staleTime: 30000,
  })
}
