// frontend/src/app/monitoring/components/AlertHistoryTab.tsx
// Purpose: Display alert history with severity filter and acknowledge action
// NOT for: Alert config CRUD (that's in AlertRulesTab)

'use client'

import { useState } from 'react'
import { useAlerts, useAcknowledgeAlert } from '@/lib/hooks/useMonitoring'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const SEVERITIES = ['all', 'info', 'warning', 'critical'] as const

const SEVERITY_COLORS: Record<string, string> = {
  info: 'border-blue-700 text-blue-400',
  warning: 'border-yellow-700 text-yellow-400',
  critical: 'border-red-700 text-red-400',
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function AlertHistoryTab() {
  const [severity, setSeverity] = useState<string>('all')
  const { data, isLoading } = useAlerts(severity === 'all' ? undefined : severity)
  const ackMutation = useAcknowledgeAlert()

  return (
    <div className="space-y-6">
      {/* Severity filter */}
      <div className="flex gap-2">
        {SEVERITIES.map((s) => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm transition-colors',
              severity === s
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Alert list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
      ) : !data?.items.length ? (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          No alerts to display.
        </div>
      ) : (
        <div className="space-y-2">
          {data.items.map((alert) => (
            <div
              key={alert.id}
              className={cn(
                'flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] px-5 py-3',
                alert.acknowledged && 'opacity-50'
              )}
            >
              <div className="flex items-center gap-4">
                <span className={`rounded-full border bg-white/5 px-2.5 py-0.5 text-xs ${SEVERITY_COLORS[alert.severity] || 'border-gray-700 text-gray-400'}`}>
                  {alert.severity}
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{alert.title}</p>
                  <p className="text-xs text-gray-500 line-clamp-1">{alert.message}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">
                  {timeAgo(alert.triggered_at)}
                </span>

                {!alert.acknowledged && (
                  <button
                    onClick={() => ackMutation.mutate(alert.id)}
                    className="flex items-center gap-1 rounded-md bg-white/5 px-2.5 py-1 text-xs text-gray-300 transition-colors hover:bg-white/10"
                    title="Acknowledge"
                  >
                    <Check className="h-3 w-3" />
                    Ack
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
