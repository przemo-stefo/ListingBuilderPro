// frontend/src/lib/compliance.ts
// Purpose: API calls for the Compliance Guard — upload template, list/get reports
// NOT for: React hooks or UI logic (those are in hooks/useCompliance.ts)

import { apiClient, apiRequest } from './client'
import type {
  ComplianceReportResponse,
  ComplianceReportsListResponse,
} from '../types'

// WHY: Template validation can be slow for large files (1000+ products)
const COMPLIANCE_TIMEOUT = 60_000

export interface ComplianceReportsParams {
  limit?: number
  offset?: number
  marketplace?: string
}

// WHY: File upload needs FormData, not JSON — uses apiClient directly to set multipart headers
export async function uploadComplianceFile(
  file: File,
  marketplace?: string
): Promise<ComplianceReportResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (marketplace) {
    formData.append('marketplace', marketplace)
  }

  const response = await apiClient.post(
    '/compliance/validate',
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
