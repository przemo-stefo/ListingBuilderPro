// frontend/src/app/catalog-health/components/DashboardTab.tsx
// Purpose: Dashboard overview stats for Catalog Health
// NOT for: Scan actions or issue list (those are in ScanTab/IssuesTab)

'use client'

import Link from 'next/link'
import { useCatalogDashboard, useCatalogHealthStatus } from '@/lib/hooks/useCatalogHealth'
import { Activity, AlertTriangle, CheckCircle, Search, Clock, FileSearch, Wrench, ArrowRight } from 'lucide-react'

interface DashboardTabProps {
  onGoToScan?: () => void
}

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

export default function DashboardTab({ onGoToScan }: DashboardTabProps) {
  const { data, isLoading, error } = useCatalogDashboard()
  const { data: status } = useCatalogHealthStatus()

  const credentialsOk = status?.credentials_configured && status?.has_refresh_token

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

  // WHY: Show onboarding when user has never scanned — empty dashboard with zeros is confusing
  if (data.total_scans === 0) {
    return (
      <div className="space-y-6">
        {/* Step 1: Connect Amazon (shown only when not connected) */}
        {!credentialsOk && (
          <div className="rounded-lg border border-amber-900 bg-amber-950/30 p-5">
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              <h3 className="text-sm font-medium text-amber-300">Krok 1: Polacz konto Amazon</h3>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Aby przeskanowac katalog, najpierw polacz swoje konto Amazon Seller Central.
              Uzyskamy dostep do danych katalogu przez Amazon SP-API.
            </p>
            <Link
              href="/integrations"
              className="inline-flex items-center gap-2 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 transition-colors"
            >
              Polacz konto Amazon
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}

        {/* Connected confirmation */}
        {credentialsOk && (
          <div className="rounded-lg border border-green-900 bg-green-950/30 p-5">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <span className="text-sm font-medium text-green-300">Konto Amazon polaczone — mozesz uruchomic skan</span>
            </div>
          </div>
        )}

        {/* How it works */}
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-6">
          <h3 className="mb-4 text-lg font-medium text-white">Jak to dziala?</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="flex gap-3">
              <div className="rounded-md bg-blue-500/10 p-2 h-fit">
                <FileSearch className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">1. Skan katalogowy</p>
                <p className="text-xs text-gray-400">
                  Pobieramy raporty z Amazon (listingi, ukryte oferty, zablokowany inventory)
                  i analizujemy kazdy produkt.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="rounded-md bg-amber-500/10 p-2 h-fit">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">2. Wykrywanie problemow</p>
                <p className="text-xs text-gray-400">
                  Identyfikujemy zepsute warianty, osierocone ASIN-y, brakujace atrybuty,
                  ukryte listingi i problemy z cenami.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="rounded-md bg-green-500/10 p-2 h-fit">
                <Wrench className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">3. Naprawy jednym kliknieciem</p>
                <p className="text-xs text-gray-400">
                  Dla kazdego problemu generujemy propozycje naprawy.
                  Mozesz ja zastosowac jednym kliknieciem przez SP-API.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Detectable issues list */}
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-6">
          <h3 className="mb-3 text-sm font-medium text-gray-300">Wykrywane problemy</h3>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {Object.entries(ISSUE_TYPE_LABELS).map(([key, label]) => (
              <div key={key} className="flex items-start gap-2">
                <Search className="h-3.5 w-3.5 mt-0.5 text-gray-500 shrink-0" />
                <div>
                  <span className="text-sm text-gray-300">{label}</span>
                  {ISSUE_TYPE_TOOLTIPS[key] && (
                    <p className="text-xs text-gray-500">{ISSUE_TYPE_TOOLTIPS[key]}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA to scan */}
        {credentialsOk && onGoToScan && (
          <button
            onClick={onGoToScan}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-white px-4 py-3 text-sm font-medium text-black transition-colors hover:bg-gray-200"
          >
            Rozpocznij pierwszy skan
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }

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
