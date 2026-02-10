// frontend/src/app/monitoring/components/TracesTab.tsx
// Purpose: Observability tab — token usage, latency per span, cost per optimization
// NOT for: Modifying traces (read-only view)

'use client'

import { useTraces, useTraceStats } from '@/lib/hooks/useMonitoring'
import { Activity, Zap, Timer, DollarSign } from 'lucide-react'

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Activity
  label: string
  value: string | number
  sub?: string
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-md bg-white/5 p-2">
          <Icon className="h-5 w-5 text-gray-400" />
        </div>
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {sub && <p className="text-xs text-gray-500">{sub}</p>}
        </div>
      </div>
    </div>
  )
}

export default function TracesTab() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useTraceStats()
  const { data: traces, isLoading: tracesLoading, error: tracesError } = useTraces()

  const isLoading = statsLoading || tracesLoading
  const error = statsError || tracesError

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="mb-3 h-8 animate-pulse rounded bg-white/5" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-900 bg-red-950/30 p-4 text-sm text-red-400">
        Failed to load traces: {error.message}
      </div>
    )
  }

  if (!stats || !traces) return null

  const items = traces.items

  return (
    <div className="space-y-6">
      {/* WHY: 4 stat cards — quick glance at token/cost/latency aggregates */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Total Runs" value={stats.runs_with_traces} />
        <StatCard
          icon={Zap}
          label="Avg Tokens/Run"
          value={stats.avg_tokens_per_run.toLocaleString()}
        />
        <StatCard
          icon={Timer}
          label="Avg Latency"
          value={`${(stats.avg_duration_ms / 1000).toFixed(1)}s`}
        />
        <StatCard
          icon={DollarSign}
          label="Total Cost"
          value={`$${stats.total_cost_usd.toFixed(4)}`}
          sub={`${stats.total_tokens.toLocaleString()} total tokens`}
        />
      </div>

      {/* WHY: Table of recent traces so user can inspect individual runs */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A]">
        <div className="border-b border-gray-800 px-5 py-3">
          <p className="text-sm font-medium text-gray-400">Recent Traces</p>
        </div>

        {items.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-gray-500">
            No traces yet. Run an optimization to see trace data here.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-gray-500">
                <th className="px-5 py-2 font-medium">Product</th>
                <th className="px-5 py-2 font-medium">Date</th>
                <th className="px-5 py-2 font-medium text-right">Tokens</th>
                <th className="px-5 py-2 font-medium text-right">Duration</th>
                <th className="px-5 py-2 font-medium text-right">Cost</th>
                <th className="px-5 py-2 font-medium text-right">Spans</th>
              </tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id} className="border-b border-gray-800/50 hover:bg-white/[0.02]">
                  <td className="max-w-[280px] truncate px-5 py-3 text-white">
                    {t.product_title}
                  </td>
                  <td className="px-5 py-3 text-gray-400">
                    {t.created_at ? new Date(t.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-5 py-3 text-right text-gray-300">
                    {t.total_tokens != null ? t.total_tokens.toLocaleString() : '-'}
                  </td>
                  <td className="px-5 py-3 text-right text-gray-300">
                    {t.total_duration_ms != null
                      ? `${(t.total_duration_ms / 1000).toFixed(1)}s`
                      : '-'}
                  </td>
                  <td className="px-5 py-3 text-right text-gray-300">
                    {t.estimated_cost_usd != null
                      ? `$${t.estimated_cost_usd.toFixed(4)}`
                      : '-'}
                  </td>
                  <td className="px-5 py-3 text-right text-gray-300">
                    {t.span_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
