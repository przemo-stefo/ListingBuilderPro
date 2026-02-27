// frontend/src/lib/compliance.ts
// Purpose: API calls for the Compliance Guard — upload template, list/get reports
// NOT for: React hooks or UI logic (those are in hooks/useCompliance.ts)

import { apiClient, apiRequest } from './client'
import type {
  ComplianceReportResponse,
  ComplianceReportsListResponse,
} from '../types'

// Audit types (inline — no separate types file needed)
export interface AuditIssue {
  field: string
  severity: string
  message: string
  fix_suggestion: string | null
}

export interface AuditResult {
  source_url: string
  source_id: string
  marketplace: string
  product_title: string
  overall_status: string
  score: number
  issues: AuditIssue[]
  product_data: Record<string, unknown>
}

// WHY: Template validation can be slow for large files (1000+ products)
const COMPLIANCE_TIMEOUT = 60_000

export interface ComplianceReportsParams {
  limit?: number
  offset?: number
  marketplace?: string
}

// WHY: File upload needs FormData, not JSON — uses apiClient directly to set multipart headers
// WHY: marketplace sent as query param (not FormData) — backend reads it via Query(), not Form()
export async function uploadComplianceFile(
  file: File,
  marketplace?: string
): Promise<ComplianceReportResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const params = marketplace ? `?marketplace=${encodeURIComponent(marketplace)}` : ''

  const response = await apiClient.post(
    `/compliance/validate${params}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: COMPLIANCE_TIMEOUT,
    }
  )

  return response.data
}

export async function getComplianceReports(
  params?: ComplianceReportsParams
): Promise<ComplianceReportsListResponse> {
  const response = await apiRequest<ComplianceReportsListResponse>(
    'get',
    '/compliance/reports',
    undefined,
    params as Record<string, unknown>
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

export async function auditProductCard(
  url: string,
  marketplace: string = 'allegro'
): Promise<AuditResult> {
  const response = await apiRequest<AuditResult>(
    'post',
    '/compliance/audit',
    { url, marketplace }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getComplianceReport(
  reportId: string
): Promise<ComplianceReportResponse> {
  const response = await apiRequest<ComplianceReportResponse>(
    'get',
    `/compliance/reports/${reportId}`
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
