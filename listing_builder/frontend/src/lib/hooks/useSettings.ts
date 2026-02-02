// frontend/src/lib/hooks/useSettings.ts
// Purpose: React Query hooks for settings data fetching and mutations
// NOT for: Direct API calls (those are in lib/api/settings.ts)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSettings, updateSettings } from '../api/settings'
import type { UpdateSettingsPayload } from '../types'
import { useToast } from './useToast'

// WHY: Separate query hook so components can read settings without mutation logic
export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
    staleTime: 30000,
  })
}

// WHY: Follows useDeleteProduct pattern — invalidate + toast on success/error
export function useUpdateSettings() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: UpdateSettingsPayload) => updateSettings(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast({
        title: 'Settings saved',
        description: 'Your settings have been updated successfully.',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to save settings',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
