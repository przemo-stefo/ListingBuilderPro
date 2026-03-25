// frontend/src/app/catalog-health/components/DashboardTab.tsx
// Purpose: Dashboard overview stats for Catalog Health
// NOT for: Scan actions or issue list (those are in ScanTab/IssuesTab)

'use client'

import { useCatalogDashboard } from '@/lib/hooks/useCatalogHealth'
import { Activity, AlertTriangle, CheckCircle, Search, Clock } from 'lucide-react'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400',
  warning: 'bg-amber-500/20 text-amber-400',
  info: 'bg-blue-500/20 text-blue-400',
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'Krytyczny',
  warning: 'Ostrzezenie',
  info: 'Informacja',
}

const ISSUE_TYPE_LABELS: Record<string, string> = {
  broken_variation: 'Zepsute warianty',
  orphaned_asin: 'Osierocone ASIN',
  missing_attribute: 'Brakujace atrybuty',
  suppressed_listing: 'Ukryte listingi',
  stranded_inventory: 'Zablokowany inventory',
  low_quality_image: 'Slabe zdjecia',
  invalid_price: 'Nieprawidlowa cena',
}

const ISSUE_TYPE_TOOLTIPS: Record<string, string> = {
  broken_variation: 'Produkt-dziecko wskazuje na parenta ktory nie istnieje lub nie zawiera tego dziecka',
  orphaned_asin: 'ASIN bez powiazania z produktem nadrzednym — nie wyswietla sie w wynikach wyszukiwania',
  missing_attribute: 'Listing nie ma wymaganych atrybutow — moze byc ukryty lub odrzucony przez Amazon',
  suppressed_listing: 'Amazon ukryl listing z powodu braku danych lub naruszenia zasad',
  stranded_inventory: 'Towar w magazynie FBA nie ma aktywnego listingu — generuje koszty magazynowe',
  low_quality_image: 'Zdjecie nie spelnia wymagan Amazon (rozmiar, tlo, jakosc)',
  invalid_price: 'Cena poza zakresem akceptowanym przez Amazon lub nizsza niz koszt',
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color = 'bg-white/5',
}: {
  icon: typeof Activity
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
      <div className="flex items-center gap-3">
        <div className={`rounded-md p-2 ${color}`}>
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
  const { data, isLoading, error } = useCatalogDashboard()

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
        Blad ladowania dashboardu: {error.message}
      </div>
    )
  }

  if (!data) return null

  const lastScanDate = data.last_scan?.completed_at
    ? new Date(data.last_scan.completed_at).toLocaleString('pl-PL')
    : 'Brak skanow'

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={Search} label="Laczna liczba skanow" value={data.total_scans} />
        <StatCard icon={AlertTriangle} label="Wykryte problemy" value={data.total_issues} color="bg-red-500/10" />
        <StatCard icon={CheckCircle} label="Naprawione" value={data.total_fixed} color="bg-green-500/10" />
        <StatCard icon={Clock} label="Ostatni skan" value={lastScanDate} />
      </div>

      {/* Issues breakdown */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* By severity */}
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          <h3 className="mb-3 text-sm font-medium text-gray-300">Problemy wg powaznosci</h3>
          {Object.keys(data.issues_by_severity).length === 0 ? (
            <p className="text-sm text-gray-500">Brak danych — uruchom skan</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(data.issues_by_severity).map(([severity, count]) => (
                <div key={severity} className="flex items-center justify-between">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${SEVERITY_COLORS[severity] || 'bg-gray-500/20 text-gray-400'}`}>
                    {SEVERITY_LABELS[severity] || severity}
                  </span>
                  <span className="text-sm font-medium text-white">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* By type — with tooltips */}
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          <h3 className="mb-3 text-sm font-medium text-gray-300">Problemy wg typu</h3>
          {Object.keys(data.issues_by_type).length === 0 ? (
            <p className="text-sm text-gray-500">Brak danych — uruchom skan</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(data.issues_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-400" title={ISSUE_TYPE_TOOLTIPS[type]}>
                    {ISSUE_TYPE_LABELS[type] || type}
                  </span>
                  <span className="text-sm font-medium text-white">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
