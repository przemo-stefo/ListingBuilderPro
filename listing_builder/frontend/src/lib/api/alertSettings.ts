// frontend/src/lib/api/alertSettings.ts
// Purpose: API calls for Sellerboard-style alert settings
// NOT for: React hooks or UI components

import { apiRequest } from './client'

export interface AlertTypeInfo {
  type: string
  label: string
  category: string
  data_source: string
  default_priority: string
  active: boolean
}

export interface AlertSettingResponse extends AlertTypeInfo {
  alert_type: string
  priority: string
  notify_in_app: boolean
  notify_email: boolean
  email_recipients: string[]
  enabled: boolean
}

export interface AlertTypeSettingPayload {
  alert_type: string
  priority: string
  notify_in_app: boolean
  notify_email: boolean
  email_recipients: string[]
  enabled: boolean
}

export async function fetchAlertTypes(): Promise<AlertTypeInfo[]> {
  const response = await apiRequest<AlertTypeInfo[]>('get', '/alert-settings/types')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchAlertSettings(): Promise<AlertSettingResponse[]> {
  const response = await apiRequest<AlertSettingResponse[]>('get', '/alert-settings')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function updateAlertSettings(
  settings: AlertTypeSettingPayload[]
): Promise<{ status: string; count: number }> {
  const response = await apiRequest<{ status: string; count: number }>(
    'put', '/alert-settings', { settings }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function toggleAlertSetting(
  alertType: string
): Promise<{ alert_type: string; enabled: boolean }> {
  const response = await apiRequest<{ alert_type: string; enabled: boolean }>(
    'patch', `/alert-settings/${alertType}`
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}
