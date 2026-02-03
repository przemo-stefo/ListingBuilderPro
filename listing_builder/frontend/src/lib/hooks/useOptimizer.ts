// frontend/src/lib/hooks/useOptimizer.ts
// Purpose: React Query hooks for the Listing Optimizer
// NOT for: Direct API calls (those are in lib/api/optimizer.ts)

import { useMutation, useQuery } from '@tanstack/react-query'
import { generateListing, generateBatch, scrapeForOptimizer, checkOptimizerHealth } from '../api/optimizer'
import type { OptimizerRequest, BatchOptimizerRequest } from '../types'
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

export function useBatchOptimizer() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: BatchOptimizerRequest) => generateBatch(payload),
    onError: (error: Error) => {
      toast({
        title: 'Batch optimization failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

export function useScrapeForOptimizer() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (urls: string[]) => scrapeForOptimizer(urls),
    onError: (error: Error) => {
      toast({
        title: 'Scraping failed',
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
