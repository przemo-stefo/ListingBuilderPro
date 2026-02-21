// frontend/src/lib/hooks/useAlertSettings.ts
// Purpose: React Query hooks for alert settings
// NOT for: Direct API calls or UI logic

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchAlertSettings,
  updateAlertSettings,
  toggleAlertSetting,
} from '../api/alertSettings'
import type { AlertTypeSettingPayload } from '../api/alertSettings'
import { useToast } from './useToast'

const STALE_TIME = 30_000

export function useAlertSettings() {
  return useQuery({
    queryKey: ['alert-settings'],
    queryFn: fetchAlertSettings,
    staleTime: STALE_TIME,
  })
}

export function useUpdateAlertSettings() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (settings: AlertTypeSettingPayload[]) => updateAlertSettings(settings),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-settings'] })
      toast({ title: 'Alert settings saved' })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to save settings', description: error.message, variant: 'destructive' })
    },
  })
}

export function useToggleAlertSetting() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (alertType: string) => toggleAlertSetting(alertType),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-settings'] })
    },
  })
}
