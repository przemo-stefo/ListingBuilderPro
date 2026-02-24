// frontend/src/app/compliance/components/AlertsTab.tsx
// Purpose: Alerts view with Active/Resolved/All filter
// NOT for: Single alert card rendering (that's AlertCard)

'use client'

import { useState } from 'react'
import { CheckCircle2, Loader2, Bell } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlerts, useAcknowledgeAlert } from '@/lib/hooks/useMonitoring'
import type { MonitoringAlert } from '@/lib/types'
import AlertCard from './AlertCard'

type AlertFilter = 'active' | 'resolved' | 'all'

const FILTER_OPTIONS: { value: AlertFilter; label: string }[] = [
  { value: 'active', label: 'Aktywne' },
  { value: 'resolved', label: 'Rozwiązane' },
  { value: 'all', label: 'Wszystkie' },
]

export default function AlertsTab() {
  const alertsQuery = useAlerts()
  const ackMutation = useAcknowledgeAlert()
  const [filter, setFilter] = useState<AlertFilter>('active')

  const alerts = (alertsQuery.data?.items ?? []) as MonitoringAlert[]
  const unacknowledged = alerts.filter((a) => !a.acknowledged)
  const acknowledged = alerts.filter((a) => a.acknowledged)
  const criticalCount = unacknowledged.filter((a) => a.severity === 'critical').length
  const warningCount = unacknowledged.filter((a) => a.severity === 'warning').length

  // WHY: Filter determines which alerts to show
  const filteredAlerts =
    filter === 'active' ? unacknowledged :
    filter === 'resolved' ? acknowledged :
    alerts

  if (alertsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with counts + filter */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Bell className="h-5 w-5 text-red-400" />
            Alerty
          </h2>
          <div className="flex gap-2">
            {criticalCount > 0 && (
              <span className="rounded-full bg-red-500/10 px-3 py-0.5 text-xs font-medium text-red-400">
                {criticalCount} krytycznych
              </span>
            )}
            {warningCount > 0 && (
              <span className="rounded-full bg-yellow-500/10 px-3 py-0.5 text-xs font-medium text-yellow-400">
                {warningCount} ostrzeżeń
              </span>
            )}
          </div>
        </div>

        {/* WHY: Filter toggle — Active/Resolved/All */}
        <div className="flex rounded-lg border border-gray-800 p-0.5">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={cn(
                'rounded-md px-3 py-1 text-xs font-medium transition-colors',
                filter === opt.value
                  ? 'bg-white/10 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              {opt.label}
              {opt.value === 'active' && unacknowledged.length > 0 && (
                <span className="ml-1.5 text-[10px] text-gray-600">{unacknowledged.length}</span>
              )}
              {opt.value === 'resolved' && acknowledged.length > 0 && (
                <span className="ml-1.5 text-[10px] text-gray-600">{acknowledged.length}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {filteredAlerts.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-10 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-green-400 mb-3" />
          <p className="text-white font-medium">
            {filter === 'active' ? 'Brak aktywnych alertów' : filter === 'resolved' ? 'Brak rozwiązanych alertów' : 'Brak alertów'}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {filter === 'active' ? 'Wszystko wygląda dobrze!' : 'Nie ma jeszcze żadnych alertów w tej kategorii.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={() => ackMutation.mutate(alert.id)}
              isAcknowledging={ackMutation.isPending}
              isResolved={alert.acknowledged}
            />
          ))}
        </div>
      )}
    </div>
  )
}
