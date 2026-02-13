// frontend/src/app/compliance/components/DashboardTab.tsx
// Purpose: Panel Glowny — stats, marketplace status, compliance scores, recent activity
// NOT for: Alert management or file uploads (those are separate tabs)

'use client'

import {
  AlertTriangle,
  AlertCircle,
  Package,
  ShieldCheck,
  ArrowRight,
  Clock,
  FileText,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMonitoringDashboard, useAlerts, useTrackedProducts } from '@/lib/hooks/useMonitoring'
import { useComplianceReports } from '@/lib/hooks/useCompliance'
import { useEprReports } from '@/lib/hooks/useEpr'
import type { MonitoringAlert, EprReport } from '@/lib/types'

// WHY: Maps EPR report status to a progress percentage for the visual bar
function eprStatusToProgress(status: string): number {
  switch (status) {
    case 'completed': return 100
    case 'processing': return 60
    case 'pending': return 20
    case 'failed': return 0
    default: return 0
  }
}

// WHY: Map marketplace_id to country flag for visual consistency
const MARKETPLACE_ID_FLAGS: Record<string, string> = {
  A1PA6795UKMFR9: '🇩🇪',
  A1RKKUPIHCS9HS: '🇪🇸',
  A13V1IB3VIYZZH: '🇫🇷',
  A1F83G8C2ARO7P: '🇬🇧',
  APJ6JRA9NG5V4: '🇮🇹',
  A2NODRKZP88ZB9: '🇸🇪',
  A1805IZSGTT6HS: '🇳🇱',
  A2Q3Y263D00KWC: '🇧🇷',
}

const MARKETPLACE_FLAGS: Record<string, string> = {
  amazon: '🇩🇪',
  ebay: '🇬🇧',
  kaufland: '🇩🇪',
  allegro: '🇵🇱',
  shopify: '🌍',
  otto: '🇩🇪',
  etsy: '🇺🇸',
}

interface DashboardTabProps {
  onNavigate: (tab: string) => void
}

export default function DashboardTab({ onNavigate }: DashboardTabProps) {
  const dashboard = useMonitoringDashboard()
  const alertsQuery = useAlerts()
  const trackedQuery = useTrackedProducts()
  const reportsQuery = useComplianceReports({ limit: 5 })
  const eprQuery = useEprReports()

  const isLoading = dashboard.isLoading || alertsQuery.isLoading

  // WHY: Count critical vs warning alerts from real data
  const alerts = (alertsQuery.data?.items ?? []) as MonitoringAlert[]
  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.acknowledged).length
  const warningCount = alerts.filter((a) => a.severity === 'warning' && !a.acknowledged).length
  const trackedCount = dashboard.data?.tracked_products ?? 0

  // WHY: Compliance % = average from latest reports, fallback 0
  const reports = reportsQuery.data?.items ?? []
  const compliancePct = reports.length > 0
    ? Math.round(reports.reduce((sum, r) => sum + r.overall_score, 0) / reports.length)
    : 0

  // WHY: Group tracked products by marketplace for status cards
  const tracked = trackedQuery.data?.items ?? []
  const marketplaceGroups: Record<string, number> = {}
  for (const p of tracked) {
    marketplaceGroups[p.marketplace] = (marketplaceGroups[p.marketplace] ?? 0) + 1
  }

  // WHY: Recent activity = last 4 alerts for the timeline
  const recentAlerts = alerts.slice(0, 4)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 4 stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Krytycznych"
          value={criticalCount}
          icon={AlertCircle}
          color="red"
        />
        <StatCard
          label="Ostrzeżeń"
          value={warningCount}
          icon={AlertTriangle}
          color="yellow"
        />
        <StatCard
          label="Produktów"
          value={trackedCount}
          icon={Package}
          color="blue"
        />
        <StatCard
          label="Zgodność"
          value={`${compliancePct}%`}
          icon={ShieldCheck}
          color="green"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Raporty EPR */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-400" />
              Raporty EPR
            </h3>
            <button
              onClick={() => onNavigate('epr')}
              className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
            >
              Wszystkie <ArrowRight className="h-3 w-3" />
            </button>
          </div>
          <EprReportsList reports={eprQuery.data?.reports ?? []} isLoading={eprQuery.isLoading} />
        </div>

        {/* Status Marketplace */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
          <h3 className="mb-4 text-sm font-semibold text-white flex items-center gap-2">
            <Package className="h-4 w-4 text-gray-400" />
            Status Marketplace
          </h3>
          {Object.keys(marketplaceGroups).length === 0 ? (
            <p className="text-sm text-gray-500">Brak śledzonych produktów</p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(marketplaceGroups).map(([mp, count]) => {
                const mpAlerts = alerts.filter(
                  (a) => a.details?.marketplace === mp && !a.acknowledged
                ).length
                return (
                  <div key={mp} className="rounded-lg border border-gray-700 bg-[#121212] p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{MARKETPLACE_FLAGS[mp] ?? '🌍'}</span>
                      <span className="text-sm font-medium text-white capitalize">{mp}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span>{count} prod.</span>
                      {mpAlerts > 0 && (
                        <span className="text-red-400">{mpAlerts} alertów</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Wynik Compliance */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
          <h3 className="mb-4 text-sm font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-green-400" />
            Wynik Compliance
          </h3>
          {[
            { label: 'WEEE', score: 78 },
            { label: 'Opakowania', score: 65 },
            { label: 'Baterie', score: 45 },
            { label: 'CE Marking', score: 90 },
          ].map((item) => (
            <div key={item.label} className="mb-3">
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-300">{item.label}</span>
                <span className={cn(
                  'text-sm font-medium',
                  item.score >= 80 ? 'text-green-400' : item.score >= 60 ? 'text-yellow-400' : 'text-red-400'
                )}>
                  {item.score}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-gray-800">
                <div
                  className={cn(
                    'h-2 rounded-full',
                    item.score >= 80 ? 'bg-green-500' : item.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  )}
                  style={{ width: `${item.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Szybkie Akcje */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
          <h3 className="mb-4 text-sm font-semibold text-white">Szybkie Akcje</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Sprawdź plik', tab: 'upload', color: 'bg-green-500/10 text-green-400 border-green-500/20' },
              { label: 'Alerty', tab: 'alerts', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
              { label: 'Ustawienia alertów', tab: 'settings', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
              { label: 'Integracje', tab: 'integrations', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
            ].map((a) => (
              <button
                key={a.tab}
                onClick={() => onNavigate(a.tab)}
                className={cn(
                  'flex items-center justify-between rounded-lg border p-3 text-sm font-medium transition-colors hover:opacity-80',
                  a.color
                )}
              >
                {a.label}
                <ArrowRight className="h-4 w-4" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ostatnia Aktywnosc */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <h3 className="mb-4 text-sm font-semibold text-white flex items-center gap-2">
          <Clock className="h-4 w-4 text-gray-400" />
          Ostatnia Aktywność
        </h3>
        {recentAlerts.length === 0 ? (
          <p className="text-sm text-gray-500">Brak ostatniej aktywności</p>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 rounded-lg bg-[#121212] p-3">
                {alert.severity === 'critical' ? (
                  <AlertCircle className="h-4 w-4 mt-0.5 text-red-400 shrink-0" />
                ) : (
                  <AlertTriangle className="h-4 w-4 mt-0.5 text-yellow-400 shrink-0" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-white truncate">{alert.title}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(alert.triggered_at).toLocaleString('pl-PL')}
                  </p>
                </div>
                <span className={cn(
                  'shrink-0 rounded px-2 py-0.5 text-[10px] font-medium',
                  alert.severity === 'critical'
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-yellow-500/10 text-yellow-400'
                )}>
                  {alert.severity === 'critical' ? 'KRYTYCZNY' : 'OSTRZEŻENIE'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EprReportsList({ reports, isLoading }: { reports: EprReport[]; isLoading: boolean }) {
  if (isLoading) {
    return <div className="h-20 animate-pulse rounded-lg bg-gray-800" />
  }
  if (reports.length === 0) {
    return <p className="text-sm text-gray-500">Brak raportów EPR</p>
  }
  // WHY: Show max 4 recent reports in dashboard summary
  return (
    <div className="space-y-4">
      {reports.slice(0, 4).map((r) => {
        const progress = eprStatusToProgress(r.status)
        const flag = MARKETPLACE_ID_FLAGS[r.marketplace_id] ?? '🌍'
        return (
          <div key={r.id}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-300">
                {flag} {r.report_type}
              </span>
              <span className={cn(
                'text-xs',
                r.status === 'completed' ? 'text-green-400' :
                r.status === 'failed' ? 'text-red-400' : 'text-yellow-400'
              )}>
                {r.status === 'completed' ? 'Ukończony' :
                 r.status === 'failed' ? 'Błąd' :
                 r.status === 'processing' ? 'Przetwarzanie' : 'Oczekujący'}
              </span>
            </div>
            <div className="h-2 rounded-full bg-gray-800">
              <div
                className={cn(
                  'h-2 rounded-full transition-all',
                  progress >= 60 ? 'bg-green-500' : progress >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                )}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: string | number
  icon: typeof AlertCircle
  color: 'red' | 'yellow' | 'blue' | 'green'
}) {
  const colors = {
    red: 'bg-red-500/10 text-red-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-green-500/10 text-green-400',
  }
  const iconBg = {
    red: 'bg-red-500/10',
    yellow: 'bg-yellow-500/10',
    blue: 'bg-blue-500/10',
    green: 'bg-green-500/10',
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
      <div className="flex items-center gap-3">
        <div className={cn('rounded-lg p-2', iconBg[color])}>
          <Icon className={cn('h-5 w-5', colors[color].split(' ')[1])} />
        </div>
        <div>
          <p className="text-xs text-gray-400">{label}</p>
          <p className={cn('text-2xl font-bold', colors[color].split(' ')[1])}>{value}</p>
        </div>
      </div>
    </div>
  )
}
