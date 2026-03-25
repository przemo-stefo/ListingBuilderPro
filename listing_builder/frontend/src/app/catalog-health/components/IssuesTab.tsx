// frontend/src/app/catalog-health/components/IssuesTab.tsx
// Purpose: Paginated issues list with severity/type filters and one-click fix
// NOT for: Scan management (that's ScanTab)

'use client'

import { useState } from 'react'
import { useScanIssues, useApplyFix } from '@/lib/hooks/useCatalogHealth'
import type { CatalogIssue } from '@/lib/api/catalog-health'
import { AlertTriangle, AlertCircle, Info, Wrench, Loader2, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const SEVERITY_CONFIG: Record<string, { icon: typeof AlertTriangle; color: string; bg: string; label: string }> = {
  critical: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/20', label: 'Krytyczny' },
  warning: { icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Ostrzezenie' },
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Informacja' },
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
  orphaned_asin: 'ASIN bez powiazania z produktem nadrzednym — nie wyswietla sie w wynikach',
  missing_attribute: 'Listing nie ma wymaganych atrybutow — moze byc ukryty przez Amazon',
  suppressed_listing: 'Amazon ukryl listing z powodu braku danych lub naruszenia zasad',
  stranded_inventory: 'Towar w FBA nie ma aktywnego listingu — generuje koszty magazynowe',
  low_quality_image: 'Zdjecie nie spelnia wymagan Amazon (rozmiar, tlo, jakosc)',
  invalid_price: 'Cena poza zakresem akceptowanym przez Amazon',
}

const PAGE_SIZE = 20

interface IssuesTabProps {
  scanId: string
  onBack: () => void
}

export default function IssuesTab({ scanId, onBack }: IssuesTabProps) {
  const [severityFilter, setSeverityFilter] = useState<string | undefined>()
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [page, setPage] = useState(0)

  const { data, isLoading, error } = useScanIssues(scanId, {
    severity: severityFilter,
    issue_type: typeFilter,
    offset: page * PAGE_SIZE,
    limit: PAGE_SIZE,
  })

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0

  return (
    <div className="space-y-4">
      {/* Header with back button */}
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="rounded-md p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <h3 className="text-lg font-medium text-white">
          Problemy skanu {data && <span className="text-gray-500">({data.total})</span>}
        </h3>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={severityFilter || ''}
          onChange={(e) => { setSeverityFilter(e.target.value || undefined); setPage(0) }}
          className="rounded-md border border-gray-700 bg-[#121212] px-3 py-1.5 text-sm text-white focus:border-gray-500 focus:outline-none"
        >
          <option value="">Wszystkie powaznosci</option>
          <option value="critical">Krytyczny</option>
          <option value="warning">Ostrzezenie</option>
          <option value="info">Informacja</option>
        </select>
        <select
          value={typeFilter || ''}
          onChange={(e) => { setTypeFilter(e.target.value || undefined); setPage(0) }}
          className="rounded-md border border-gray-700 bg-[#121212] px-3 py-1.5 text-sm text-white focus:border-gray-500 focus:outline-none"
        >
          <option value="">Wszystkie typy</option>
          {Object.entries(ISSUE_TYPE_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>

      {/* Issues list */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-900 bg-red-950/30 p-4 text-sm text-red-400">
          {error.message}
        </div>
      ) : !data?.issues.length ? (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          Brak problemow spelniajacych kryteria
        </div>
      ) : (
        <div className="space-y-2">
          {data.issues.map((issue) => (
            <IssueRow key={issue.id} issue={issue} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-sm text-gray-400">
            {page + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}

function IssueRow({ issue }: { issue: CatalogIssue }) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [isFixing, setIsFixing] = useState(false)
  const applyFix = useApplyFix()
  const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.info
  const SevIcon = cfg.icon
  const hasFix = !!issue.fix_proposal && issue.fix_status === 'pending'

  const handleFix = () => {
    setIsFixing(true)
    applyFix.mutate(issue.id, {
      onSettled: () => {
        setIsFixing(false)
        setShowConfirm(false)
      },
    })
  }

  return (
    <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={cn('mt-0.5 rounded-md p-1.5', cfg.bg)}>
            <SevIcon className={cn('h-4 w-4', cfg.color)} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white">{issue.title}</p>
            {issue.description && (
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">{issue.description}</p>
            )}
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <span
                className="rounded bg-gray-800 px-2 py-0.5 text-[10px] font-medium text-gray-400"
                title={ISSUE_TYPE_TOOLTIPS[issue.issue_type]}
              >
                {ISSUE_TYPE_LABELS[issue.issue_type] || issue.issue_type}
              </span>
              {issue.asin && (
                <span className="text-[10px] text-gray-600">ASIN: {issue.asin}</span>
              )}
              {issue.sku && (
                <span className="text-[10px] text-gray-600">SKU: {issue.sku}</span>
              )}
              {issue.fix_status === 'applied' && (
                <span className="flex items-center gap-1 text-[10px] text-green-400">
                  <CheckCircle className="h-3 w-3" /> Naprawione
                </span>
              )}
              {issue.fix_status === 'failed' && (
                <span className="text-[10px] text-red-400">Naprawa nieudana</span>
              )}
            </div>
          </div>
        </div>

        {hasFix && !showConfirm && (
          <button
            onClick={() => setShowConfirm(true)}
            className="flex shrink-0 items-center gap-1.5 rounded-md bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
          >
            <Wrench className="h-3.5 w-3.5" />
            Napraw
          </button>
        )}
      </div>

      {/* Fix confirmation */}
      {showConfirm && (
        <div className="mt-3 rounded-md border border-gray-700 bg-[#121212] p-3">
          <p className="mb-1 text-xs font-medium text-gray-300">Co zostanie zmienione:</p>
          <p className="mb-3 text-xs text-gray-500">
            {issue.fix_proposal?.action === 'patch'
              ? `Zaktualizuje atrybuty listingu ${issue.sku || issue.asin} przez Amazon Listings API (PATCH)`
              : issue.fix_proposal?.action === 'put'
                ? `Nadpisze listing ${issue.sku || issue.asin} przez Amazon Listings API (PUT)`
                : `Zastosuje naprawe dla ${issue.sku || issue.asin}`}
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleFix}
              disabled={isFixing}
              className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {isFixing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5" />}
              Tak, napraw
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              className="rounded-md px-3 py-1.5 text-xs text-gray-400 hover:text-white"
            >
              Anuluj
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
