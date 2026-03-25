// frontend/src/lib/hooks/useCatalogHealth.ts
// Purpose: React Query hooks for Catalog Health Check module
// NOT for: Direct API calls (those are in lib/api/catalog-health.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchCatalogHealthStatus,
  fetchCatalogDashboard,
  startCatalogScan,
  fetchScanStatus,
  fetchScanIssues,
  fetchScanHistory,
  applyIssueFix,
} from '../api/catalog-health'
import { useToast } from './useToast'

const STALE_TIME = 30_000

export function useCatalogHealthStatus() {
  return useQuery({
    queryKey: ['catalog-health-status'],
    queryFn: fetchCatalogHealthStatus,
    staleTime: STALE_TIME,
  })
}

export function useCatalogDashboard() {
  return useQuery({
    queryKey: ['catalog-health-dashboard'],
    queryFn: fetchCatalogDashboard,
    staleTime: STALE_TIME,
  })
}

export function useScanHistory(offset = 0, limit = 10) {
  return useQuery({
    queryKey: ['catalog-health-scans', offset, limit],
    queryFn: () => fetchScanHistory({ offset, limit }),
    staleTime: STALE_TIME,
  })
}

export function useScanStatus(scanId: string | null) {
  return useQuery({
    queryKey: ['catalog-health-scan', scanId],
    queryFn: () => fetchScanStatus(scanId!),
    enabled: !!scanId,
    // WHY: Poll every 3s while scan is running to show progress
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'pending' || status === 'scanning' ? 3000 : false
    },
  })
}

export function useScanIssues(
  scanId: string | null,
  params?: { issue_type?: string; severity?: string; offset?: number; limit?: number }
) {
  return useQuery({
    queryKey: ['catalog-health-issues', scanId, params],
    queryFn: () => fetchScanIssues(scanId!, params),
    enabled: !!scanId,
    staleTime: STALE_TIME,
  })
}

export function useStartScan() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (marketplace: string) => startCatalogScan(marketplace),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['catalog-health-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-health-scans'] })
      toast({ title: 'Skan uruchomiony', description: 'Skan katalogu zostal rozpoczety.' })
    },
    onError: (error: Error) => {
      toast({ title: 'Blad', description: error.message, variant: 'destructive' })
    },
  })
}

export function useApplyFix() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (issueId: string) => applyIssueFix(issueId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['catalog-health-issues'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-health-dashboard'] })
      toast({ title: 'Naprawa zastosowana', description: data.message })
    },
    onError: (error: Error) => {
      toast({ title: 'Blad naprawy', description: error.message, variant: 'destructive' })
    },
  })
}
