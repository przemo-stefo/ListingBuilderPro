// frontend/src/lib/api/monitoring.ts
// Purpose: API calls for the Monitoring & Alerts system
// NOT for: React hooks or UI logic (those are in hooks/useMonitoring.ts)

import { apiRequest } from './client'
import type {
  MonitoringDashboardStats,
  TrackedProduct,
  TrackProductRequest,
  AlertConfig,
  AlertConfigCreateRequest,
  MonitoringAlert,
  TraceItem,
  TraceStats,
} from '../types'

export async function fetchDashboardStats(): Promise<MonitoringDashboardStats> {
  const response = await apiRequest<MonitoringDashboardStats>('get', '/monitoring/dashboard')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchTrackedProducts(
  marketplace?: string
): Promise<{ items: TrackedProduct[]; total: number }> {
  const params = marketplace ? { marketplace } : undefined
  const response = await apiRequest<{ items: TrackedProduct[]; total: number }>(
    'get', '/monitoring/tracked', undefined, params
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function trackProduct(body: TrackProductRequest): Promise<TrackedProduct> {
  const response = await apiRequest<TrackedProduct>('post', '/monitoring/track', body)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function untrackProduct(id: string): Promise<void> {
  const response = await apiRequest<void>('delete', `/monitoring/track/${id}`)
  if (response.error) throw new Error(response.error)
}

export async function toggleTracking(id: string): Promise<{ id: string; enabled: boolean }> {
  const response = await apiRequest<{ id: string; enabled: boolean }>(
    'patch', `/monitoring/track/${id}/toggle`
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchAlertConfigs(
  alertType?: string
): Promise<{ items: AlertConfig[]; total: number }> {
  const params = alertType ? { alert_type: alertType } : undefined
  const response = await apiRequest<{ items: AlertConfig[]; total: number }>(
    'get', '/monitoring/alerts/configs', undefined, params
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function createAlertConfig(body: AlertConfigCreateRequest): Promise<AlertConfig> {
  const response = await apiRequest<AlertConfig>('post', '/monitoring/alerts/config', body)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function deleteAlertConfig(id: string): Promise<void> {
  const response = await apiRequest<void>('delete', `/monitoring/alerts/config/${id}`)
  if (response.error) throw new Error(response.error)
}

export async function toggleAlertConfig(id: string): Promise<{ id: string; enabled: boolean }> {
  const response = await apiRequest<{ id: string; enabled: boolean }>(
    'patch', `/monitoring/alerts/config/${id}/toggle`
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchAlerts(
  severity?: string
): Promise<{ items: MonitoringAlert[]; total: number }> {
  const params = severity ? { severity } : undefined
  const response = await apiRequest<{ items: MonitoringAlert[]; total: number }>(
    'get', '/monitoring/alerts', undefined, params
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function acknowledgeAlert(id: string): Promise<void> {
  const response = await apiRequest<void>('patch', `/monitoring/alerts/${id}/ack`)
  if (response.error) throw new Error(response.error)
}

export async function fetchTraces(
  limit = 50, offset = 0
): Promise<{ items: TraceItem[]; total: number }> {
  const response = await apiRequest<{ items: TraceItem[]; total: number }>(
    'get', '/optimizer/traces', undefined, { limit, offset }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchTraceStats(): Promise<TraceStats> {
  const response = await apiRequest<TraceStats>('get', '/optimizer/traces/stats')
  if (response.error) throw new Error(response.error)
  return response.data!
}
