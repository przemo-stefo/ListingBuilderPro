// frontend/src/lib/api/settings.ts
// Purpose: Settings API calls (get and update)
// NOT for: React hooks or UI logic (those are in hooks/useSettings.ts)

import { apiRequest } from './client'
import type { SettingsResponse, UpdateSettingsPayload } from '../types'

export async function getSettings(): Promise<SettingsResponse> {
  const response = await apiRequest<SettingsResponse>('get', '/settings')

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

export async function updateSettings(
  payload: UpdateSettingsPayload
): Promise<SettingsResponse> {
  const response = await apiRequest<SettingsResponse>(
    'put',
    '/settings',
    payload
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
