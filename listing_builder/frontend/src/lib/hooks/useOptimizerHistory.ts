// frontend/src/lib/hooks/useOptimizerHistory.ts
// Purpose: React Query hooks for optimizer history
// NOT for: Direct API calls (those are in lib/api/optimizerHistory.ts)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHistory, deleteHistory } from '../api/optimizerHistory'
import { useToast } from './useToast'

export function useHistoryList(page = 1) {
  return useQuery({
    queryKey: ['optimizer-history', page],
    queryFn: () => getHistory(page),
    staleTime: 10_000,
  })
}

export function useDeleteHistory() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteHistory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['optimizer-history'] })
      toast({ title: 'Run deleted' })
    },
    onError: (error: Error) => {
      toast({ title: 'Delete failed', description: error.message, variant: 'destructive' })
    },
  })
}
