// frontend/src/lib/api/automation.ts
// Purpose: API calls for Google Workspace automation (reports, office, Google connect)
// NOT for: React hooks or UI components

import { apiRequest } from './client'

// ─── UC1: Reports ───────────────────────────────────────────────────────────

interface ReportResponse {
  status: string
  spreadsheet_id: string
  spreadsheet_url: string
  email_sent: boolean
}

export async function generateReport(params: {
  marketplace?: string
  period?: string
  send_email?: boolean
  email_to?: string
  share_with?: string
}): Promise<ReportResponse> {
  const response = await apiRequest<ReportResponse>('post', '/reports/generate', params)
  if (response.error) throw new Error(response.error)
  return response.data!
}

// ─── UC4: Google Connect ────────────────────────────────────────────────────

interface GoogleAuthorizeResponse {
  status: string
  client_id: string
  scope: string
}

interface GoogleConnectResponse {
  status: string
  email: string
  scopes: string
}

interface GoogleStatusResponse {
  status: string
  email?: string
  scopes?: string
  connected_at?: string
}

export async function getGoogleAuthorizeUrl(): Promise<GoogleAuthorizeResponse> {
  const response = await apiRequest<GoogleAuthorizeResponse>('get', '/automation/google/authorize')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function connectGoogle(code: string): Promise<GoogleConnectResponse> {
  const response = await apiRequest<GoogleConnectResponse>('post', '/automation/google/connect', { code })
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getGoogleStatus(): Promise<GoogleStatusResponse> {
  const response = await apiRequest<GoogleStatusResponse>('get', '/automation/google/status')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function disconnectGoogle(): Promise<void> {
  const response = await apiRequest<void>('delete', '/automation/google/disconnect')
  if (response.error) throw new Error(response.error)
}
