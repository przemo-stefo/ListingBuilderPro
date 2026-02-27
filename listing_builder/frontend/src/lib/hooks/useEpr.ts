// frontend/src/lib/hooks/useEpr.ts
// Purpose: React Query hooks for EPR Reports system
// NOT for: Direct API calls (those are in lib/api/epr.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchEprStatus,
  fetchEprReports,
  fetchEprReport,
  triggerEprFetch,
  deleteEprReport,
  fetchEprCountryRules,
} from '../api/epr'
import type { EprFetchRequest } from '../types'
import { useToast } from './useToast'

export function useEprStatus() {
  return useQuery({
    queryKey: ['epr-status'],
    queryFn: fetchEprStatus,
    staleTime: 60_000,
  })
}

export function useEprReports() {
  return useQuery({
    queryKey: ['epr-reports'],
    queryFn: fetchEprReports,
    staleTime: 30_000,
  })
}

export function useEprReport(id: string | null) {
  return useQuery({
    queryKey: ['epr-report', id],
    queryFn: () => fetchEprReport(id!),
    staleTime: 60_000,
    enabled: !!id,
  })
}

export function useEprFetch() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (body: EprFetchRequest) => triggerEprFetch(body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['epr-reports'] })
      // WHY: Backend returns EprReport object (no .message), use static text
      toast({ title: 'Raport EPR', description: data.message || 'Raport EPR został wygenerowany' })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd pobierania EPR', description: error.message, variant: 'destructive' })
    },
  })
}

export function useEprCountryRules() {
  return useQuery({
    queryKey: ['epr-country-rules'],
    queryFn: fetchEprCountryRules,
    staleTime: 300_000, // WHY: Country rules rarely change — 5 min cache
  })
}

export function useDeleteEprReport() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteEprReport(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['epr-reports'] })
      toast({ title: 'Raport usunięty' })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd usuwania', description: error.message, variant: 'destructive' })
    },
  })
}
