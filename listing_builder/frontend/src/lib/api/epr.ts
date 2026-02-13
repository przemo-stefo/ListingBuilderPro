// frontend/src/lib/api/epr.ts
// Purpose: API calls for the EPR Reports system (Amazon SP-API)
// NOT for: React hooks or UI logic (those are in hooks/useEpr.ts)

import { apiRequest } from './client'
import type {
  EprStatusResponse,
  EprReportsListResponse,
  EprReport,
  EprFetchRequest,
} from '../types'

export async function fetchEprStatus(): Promise<EprStatusResponse> {
  const response = await apiRequest<EprStatusResponse>('get', '/epr/status')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchEprReports(): Promise<EprReportsListResponse> {
  const response = await apiRequest<EprReportsListResponse>('get', '/epr/reports')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchEprReport(id: string): Promise<EprReport> {
  const response = await apiRequest<EprReport>('get', `/epr/reports/${id}`)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function triggerEprFetch(body: EprFetchRequest): Promise<{ message: string; report_id?: string }> {
  const response = await apiRequest<{ message: string; report_id?: string }>('post', '/epr/fetch', body)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function deleteEprReport(id: string): Promise<void> {
  const response = await apiRequest<void>('delete', `/epr/reports/${id}`)
  if (response.error) throw new Error(response.error)
}
