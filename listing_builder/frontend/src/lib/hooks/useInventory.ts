// frontend/src/lib/hooks/useInventory.ts
// Purpose: React Query hook for inventory stock level data fetching
// NOT for: Direct API calls (those are in lib/api/inventory.ts)

import { useQuery } from '@tanstack/react-query'
import { getInventory } from '../api/inventory'
import type { GetInventoryParams } from '../types'

// WHY: Same pattern as useCompetitors - React Query handles caching and refetching
export function useInventory(params?: GetInventoryParams) {
  return useQuery({
    queryKey: ['inventory', params],
    queryFn: () => getInventory(params),
    staleTime: 30000,
  })
}
