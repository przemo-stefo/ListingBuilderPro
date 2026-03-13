// frontend/src/lib/hooks/useMediaHistory.ts
// Purpose: React Query hooks for media generation history
// NOT for: Direct API calls (those are in lib/api/mediaGeneration.ts)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMediaHistory, deleteGeneration } from '../api/mediaGeneration'
import { useToast } from './useToast'

export function useMediaHistoryList(page = 1) {
  return useQuery({
    queryKey: ['media-history', page],
    queryFn: () => getMediaHistory(page),
    staleTime: 10_000,
  })
}

export function useDeleteMediaHistory() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteGeneration(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['media-history'] })
      toast({ title: 'Generacja usunieta' })
    },
    onError: (error: Error) => {
      toast({ title: 'Usuwanie nie powiodlo sie', description: error.message, variant: 'destructive' })
    },
  })
}
