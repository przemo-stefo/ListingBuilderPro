// frontend/src/lib/hooks/useOptimizer.ts
// Purpose: React Query hooks for the Listing Optimizer
// NOT for: Direct API calls (those are in lib/api/optimizer.ts)

import { useMutation, useQuery } from '@tanstack/react-query'
import { generateListing, checkOptimizerHealth } from '../api/optimizer'
import type { OptimizerRequest } from '../types'
import { useToast } from './useToast'

export function useGenerateListing() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: OptimizerRequest) => generateListing(payload),
    onError: (error: Error) => {
      toast({
        title: 'Optimization failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

export function useOptimizerHealth() {
  return useQuery({
    queryKey: ['optimizer-health'],
    queryFn: checkOptimizerHealth,
    staleTime: 30_000, // WHY: Health status doesn't change often — cache 30s
    retry: false,
  })
}
