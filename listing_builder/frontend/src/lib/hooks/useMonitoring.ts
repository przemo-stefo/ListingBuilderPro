// frontend/src/lib/hooks/useMonitoring.ts
// Purpose: React Query hooks for the Monitoring & Alerts system
// NOT for: Direct API calls (those are in lib/api/monitoring.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchDashboardStats,
  fetchTrackedProducts,
  trackProduct,
  untrackProduct,
  toggleTracking,
  fetchAlertConfigs,
  createAlertConfig,
  deleteAlertConfig,
  toggleAlertConfig,
  fetchAlerts,
  acknowledgeAlert,
} from '../api/monitoring'
import type { TrackProductRequest, AlertConfigCreateRequest } from '../types'
import { useToast } from './useToast'

const STALE_TIME = 30_000

export function useMonitoringDashboard() {
  return useQuery({
    queryKey: ['monitoring-dashboard'],
    queryFn: fetchDashboardStats,
    staleTime: STALE_TIME,
  })
}

export function useTrackedProducts(marketplace?: string) {
  return useQuery({
    queryKey: ['tracked-products', marketplace],
    queryFn: () => fetchTrackedProducts(marketplace),
    staleTime: STALE_TIME,
  })
}

export function useAlertConfigs(alertType?: string) {
  return useQuery({
    queryKey: ['alert-configs', alertType],
    queryFn: () => fetchAlertConfigs(alertType),
    staleTime: STALE_TIME,
  })
}

export function useAlerts(severity?: string) {
  return useQuery({
    queryKey: ['alerts', severity],
    queryFn: () => fetchAlerts(severity),
    staleTime: STALE_TIME,
  })
}

export function useTrackProduct() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (body: TrackProductRequest) => trackProduct(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracked-products'] })
      qc.invalidateQueries({ queryKey: ['monitoring-dashboard'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to track product', description: error.message, variant: 'destructive' })
    },
  })
}

export function useUntrackProduct() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => untrackProduct(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracked-products'] })
      qc.invalidateQueries({ queryKey: ['monitoring-dashboard'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to untrack product', description: error.message, variant: 'destructive' })
    },
  })
}

export function useToggleTracking() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => toggleTracking(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tracked-products'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to toggle tracking', description: error.message, variant: 'destructive' })
    },
  })
}

export function useCreateAlertConfig() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (body: AlertConfigCreateRequest) => createAlertConfig(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-configs'] })
      qc.invalidateQueries({ queryKey: ['monitoring-dashboard'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to create alert rule', description: error.message, variant: 'destructive' })
    },
  })
}

export function useDeleteAlertConfig() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteAlertConfig(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-configs'] })
      qc.invalidateQueries({ queryKey: ['monitoring-dashboard'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to delete alert rule', description: error.message, variant: 'destructive' })
    },
  })
}

export function useToggleAlertConfig() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => toggleAlertConfig(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-configs'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to toggle alert config', description: error.message, variant: 'destructive' })
    },
  })
}

export function useAcknowledgeAlert() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => acknowledgeAlert(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['monitoring-dashboard'] })
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to acknowledge alert', description: error.message, variant: 'destructive' })
    },
  })
}
