// frontend/src/lib/hooks/useCompetitors.ts
// Purpose: React Query hook for competitor tracking data fetching
// NOT for: Direct API calls (those are in lib/api/competitors.ts)

import { useQuery } from '@tanstack/react-query'
import { getCompetitors } from '../api/competitors'
import type { GetCompetitorsParams } from '../types'

// WHY: Same pattern as useKeywords - React Query handles caching and refetching
export function useCompetitors(params?: GetCompetitorsParams) {
  return useQuery({
    queryKey: ['competitors', params],
    queryFn: () => getCompetitors(params),
    staleTime: 30000,
  })
}
