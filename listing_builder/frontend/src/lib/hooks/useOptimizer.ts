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
    onError: (error: Error & { code?: string }) => {
      // WHY: Different messages for different error types — user knows what happened
      const code = error.code || ''
      let title = 'Optymalizacja nie powiodła się'
      let description = error.message || 'Nieoczekiwany błąd. Spróbuj ponownie.'

      if (code === '503' || error.message?.includes('przeciążony')) {
        title = 'Serwer AI przeciążony'
        description = 'Wszystkie klucze API są chwilowo wyczerpane. Spróbuj ponownie za minutę.'
      } else if (code === '504' || error.message?.includes('limit czasu')) {
        title = 'Timeout'
        description = 'Generowanie trwało zbyt długo. Spróbuj ponownie — czasem pomaga krótsza lista słów kluczowych.'
      } else if (code === '402') {
        title = 'Limit wyczerpany'
        description = error.message
      }

      toast({ title, description, variant: 'destructive' })
    },
  })
}

export function useBatchOptimizer() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: BatchOptimizerRequest) => generateBatch(payload),
    onError: (error: Error & { code?: string }) => {
      const code = error.code || ''
      let title = 'Optymalizacja zbiorcza nie powiodła się'
      let description = error.message || 'Nieoczekiwany błąd. Spróbuj ponownie.'

      if (code === '503' || error.message?.includes('przeciążony')) {
        title = 'Serwer AI przeciążony'
        description = 'Wszystkie klucze API są chwilowo wyczerpane. Spróbuj ponownie za minutę.'
      } else if (code === '504' || error.message?.includes('limit czasu')) {
        title = 'Timeout'
        description = 'Zbyt wiele produktów — spróbuj mniejszy batch.'
      } else if (code === '402') {
        title = 'Limit wyczerpany'
        description = error.message
      }

      toast({ title, description, variant: 'destructive' })
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
