// frontend/src/lib/hooks/useAutomation.ts
// Purpose: React Query hooks for Google Workspace automation
// NOT for: Direct API calls (those are in lib/api/automation.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  generateReport, getGoogleStatus, getGoogleAuthorizeUrl,
  connectGoogle, disconnectGoogle,
} from '../api/automation'
import { useToast } from './useToast'

export function useGenerateReport() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: generateReport,
    onSuccess: (data) => {
      toast({ title: 'Raport wygenerowany', description: 'Otwieranie w Google Sheets...' })
      if (data.spreadsheet_url) {
        window.open(data.spreadsheet_url, '_blank')
      }
    },
    onError: (error: Error) => {
      toast({ title: 'Blad generowania raportu', description: error.message, variant: 'destructive' })
    },
  })
}

export function useGoogleStatus() {
  return useQuery({
    queryKey: ['google-status'],
    queryFn: getGoogleStatus,
    staleTime: 60_000,
  })
}

export function useGoogleConnect() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: connectGoogle,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['google-status'] })
      toast({ title: 'Google polaczony', description: `Konto: ${data.email}` })
    },
    onError: (error: Error) => {
      toast({ title: 'Blad laczenia z Google', description: error.message, variant: 'destructive' })
    },
  })
}

export function useGoogleDisconnect() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: disconnectGoogle,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['google-status'] })
      toast({ title: 'Google rozlaczony' })
    },
    onError: (error: Error) => {
      toast({ title: 'Blad rozlaczania', description: error.message, variant: 'destructive' })
    },
  })
}
