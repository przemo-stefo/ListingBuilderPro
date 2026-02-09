// frontend/src/app/monitoring/components/DashboardTab.tsx
// Purpose: Stats overview cards for the monitoring dashboard
// NOT for: CRUD operations (those are in other tabs)

'use client'

import { useMonitoringDashboard } from '@/lib/hooks/useMonitoring'
import { Package, Bell, AlertTriangle, Clock } from 'lucide-react'

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Package
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

export default function DashboardTab() {
  const { data, isLoading, error } = useMonitoringDashboard()

  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-900 bg-red-950/30 p-4 text-sm text-red-400">
        Failed to load dashboard: {error.message}
      </div>
    )
  }

  if (!data) return null

  const lastPoll = data.last_poll
    ? new Date(data.last_poll).toLocaleString()
    : 'Never'

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={Package} label="Tracked Products" value={data.tracked_products} />
        <StatCard icon={Bell} label="Active Alert Rules" value={data.active_alerts} />
        <StatCard icon={AlertTriangle} label="Alerts Today" value={data.alerts_today} />
        <StatCard icon={Clock} label="Last Poll" value={lastPoll} />
      </div>

      {/* WHY: Show tracked products per marketplace */}
      {Object.keys(data.marketplaces).length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          <p className="mb-3 text-sm font-medium text-gray-400">Products by Marketplace</p>
          <div className="flex gap-3">
            {Object.entries(data.marketplaces).map(([marketplace, count]) => (
              <span
                key={marketplace}
                className="rounded-full border border-gray-700 bg-white/5 px-3 py-1 text-sm text-white"
              >
                {marketplace}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
