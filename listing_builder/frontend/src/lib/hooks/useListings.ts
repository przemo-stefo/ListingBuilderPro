// frontend/src/lib/hooks/useListings.ts
// Purpose: React Query hook for listings data fetching
// NOT for: Direct API calls (those are in lib/api/listings.ts)

import { useQuery } from '@tanstack/react-query'
import { getListings } from '../api/listings'
import type { GetListingsParams } from '../types'

// WHY: Same pattern as useProducts - React Query handles caching and refetching
export function useListings(params?: GetListingsParams) {
  return useQuery({
    queryKey: ['listings', params],
    queryFn: () => getListings(params),
    staleTime: 30000,
  })
}
