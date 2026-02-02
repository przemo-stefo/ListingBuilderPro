// frontend/src/lib/api/settings.ts
// Purpose: Settings API calls (get and update)
// NOT for: React hooks or UI logic (those are in hooks/useSettings.ts)

import type { SettingsResponse, UpdateSettingsPayload } from '../types'

// WHY: Uses Next.js API route (fetch) instead of apiClient — same pattern as analytics.ts
export async function getSettings(): Promise<SettingsResponse> {
  const response = await fetch('/api/settings')

  if (!response.ok) {
    throw new Error('Failed to fetch settings')
  }

  return response.json()
}

export async function updateSettings(
  payload: UpdateSettingsPayload
): Promise<SettingsResponse> {
  const response = await fetch('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error('Failed to save settings')
  }

  return response.json()
}
