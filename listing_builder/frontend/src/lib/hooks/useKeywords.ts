// frontend/src/lib/hooks/useKeywords.ts
// Purpose: React Query hook for keyword tracking data fetching
// NOT for: Direct API calls (those are in lib/api/keywords.ts)

import { useQuery } from '@tanstack/react-query'
import { getKeywords } from '../api/keywords'
import type { GetKeywordsParams } from '../types'

// WHY: Same pattern as useListings - React Query handles caching and refetching
export function useKeywords(params?: GetKeywordsParams) {
  return useQuery({
    queryKey: ['keywords', params],
    queryFn: () => getKeywords(params),
    staleTime: 30000,
  })
}
