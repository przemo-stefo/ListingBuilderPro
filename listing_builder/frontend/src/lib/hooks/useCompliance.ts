// frontend/src/lib/hooks/useCompliance.ts
// Purpose: React Query hooks for Compliance Guard — upload, list, detail
// NOT for: Direct API calls (those are in lib/api/compliance.ts)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  uploadComplianceFile,
  getComplianceReports,
  getComplianceReport,
  type ComplianceReportsParams,
} from '../api/compliance'
import { useToast } from './useToast'

export function useComplianceReports(params?: ComplianceReportsParams) {
  return useQuery({
    queryKey: ['compliance-reports', params],
    queryFn: () => getComplianceReports(params),
    staleTime: 30_000, // WHY: Reports list can change after upload — keep relatively fresh
  })
}

export function useComplianceReport(reportId: string | null) {
  return useQuery({
    queryKey: ['compliance-report', reportId],
    queryFn: () => getComplianceReport(reportId!),
    enabled: !!reportId, // WHY: Only fetch when user clicks into a specific report
    staleTime: 60_000, // WHY: Individual report data is immutable once created
  })
}

// WHY: Separate mutation for upload — invalidates reports list on success so table refreshes
export function useUploadCompliance() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, marketplace }: { file: File; marketplace?: string }) =>
      uploadComplianceFile(file, marketplace),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-reports'] })
      toast({
        title: 'Analysis complete',
        description: 'Your compliance report is ready.',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Analysis failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
