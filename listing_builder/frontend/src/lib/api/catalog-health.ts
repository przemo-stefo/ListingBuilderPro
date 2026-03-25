// frontend/src/lib/api/catalog-health.ts
// Purpose: API calls for Catalog Health Check module
// NOT for: React hooks or UI logic (those are in hooks/useCatalogHealth.ts)

import { apiRequest } from './client'

export interface CatalogScan {
  id: string
  user_id: string
  marketplace: string
  seller_id: string | null
  status: 'pending' | 'scanning' | 'completed' | 'failed'
  progress: { phase: string; percent: number } | null
  total_listings: number
  issues_found: number
  issues_fixed: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string | null
}

export interface CatalogIssue {
  id: string
  scan_id: string
  asin: string | null
  sku: string | null
  issue_type: string
  severity: 'critical' | 'warning' | 'info'
  title: string
  description: string | null
  amazon_issue_code: string | null
  fix_proposal: Record<string, unknown> | null
  fix_status: 'pending' | 'applied' | 'failed' | 'skipped'
  fix_result: Record<string, unknown> | null
  created_at: string | null
}

export interface CatalogDashboard {
  total_scans: number
  last_scan: CatalogScan | null
  issues_by_type: Record<string, number>
  issues_by_severity: Record<string, number>
  total_issues: number
  total_fixed: number
}

export interface FixResult {
  issue_id: string
  fix_status: string
  fix_result: Record<string, unknown> | null
  message: string
}

export interface CatalogHealthStatus {
  credentials_configured: boolean
  has_refresh_token: boolean
}

export async function fetchCatalogHealthStatus(): Promise<CatalogHealthStatus> {
  const res = await apiRequest<CatalogHealthStatus>('get', '/catalog-health/status')
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function fetchCatalogDashboard(): Promise<CatalogDashboard> {
  const res = await apiRequest<CatalogDashboard>('get', '/catalog-health/dashboard')
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function startCatalogScan(marketplace: string): Promise<CatalogScan> {
  const res = await apiRequest<CatalogScan>('post', '/catalog-health/scan', { marketplace })
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function fetchScanStatus(scanId: string): Promise<CatalogScan> {
  const res = await apiRequest<CatalogScan>('get', `/catalog-health/scan/${scanId}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function fetchScanIssues(
  scanId: string,
  params?: { issue_type?: string; severity?: string; offset?: number; limit?: number }
): Promise<{ issues: CatalogIssue[]; total: number }> {
  const res = await apiRequest<{ issues: CatalogIssue[]; total: number }>(
    'get', `/catalog-health/scan/${scanId}/issues`, undefined, params as Record<string, unknown>
  )
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function fetchScanHistory(
  params?: { offset?: number; limit?: number }
): Promise<{ scans: CatalogScan[]; total: number }> {
  const res = await apiRequest<{ scans: CatalogScan[]; total: number }>(
    'get', '/catalog-health/scans', undefined, params as Record<string, unknown>
  )
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function applyIssueFix(issueId: string): Promise<FixResult> {
  const res = await apiRequest<FixResult>('post', `/catalog-health/fix/${issueId}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}
