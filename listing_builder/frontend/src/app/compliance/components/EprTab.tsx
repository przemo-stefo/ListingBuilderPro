// frontend/src/app/compliance/components/EprTab.tsx
// Purpose: EPR Reports tab — status, fetch trigger, report list, detail view
// NOT for: Dashboard summary or compliance file uploads

'use client'

import { useState } from 'react'
import {
  FileBarChart,
  Download,
  Trash2,
  Eye,
  X,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEprStatus, useEprReports, useEprReport, useEprFetch, useDeleteEprReport } from '@/lib/hooks/useEpr'
import type { EprReport } from '@/lib/types'
import EprCountryRulesSection from './EprCountryRulesSection'

const STATUS_STYLES: Record<string, { label: string; cls: string }> = {
  completed: { label: 'Ukończony', cls: 'bg-green-500/10 text-green-400' },
  processing: { label: 'Przetwarzanie', cls: 'bg-blue-500/10 text-blue-400' },
  pending: { label: 'Oczekujący', cls: 'bg-yellow-500/10 text-yellow-400' },
  failed: { label: 'Błąd', cls: 'bg-red-500/10 text-red-400' },
}

const MATERIAL_LABELS: { key: keyof EprMaterialKeys; label: string }[] = [
  { key: 'paper_kg', label: 'Papier' },
  { key: 'glass_kg', label: 'Szkło' },
  { key: 'aluminum_kg', label: 'Aluminium' },
  { key: 'steel_kg', label: 'Stal' },
  { key: 'plastic_kg', label: 'Plastik' },
  { key: 'wood_kg', label: 'Drewno' },
]

// WHY: Narrow type for material weight keys used in row detail table
type EprMaterialKeys = Pick<
  import('@/lib/types').EprReportRow,
  'paper_kg' | 'glass_kg' | 'aluminum_kg' | 'steel_kg' | 'plastic_kg' | 'wood_kg'
>

export default function EprTab() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const statusQuery = useEprStatus()
  const reportsQuery = useEprReports()
  const detailQuery = useEprReport(selectedId)
  const fetchMutation = useEprFetch()
  const deleteMutation = useDeleteEprReport()

  const status = statusQuery.data
  const reports = reportsQuery.data?.reports ?? []
  const detail = detailQuery.data

  return (
    <div className="space-y-6">
      {/* Status banner */}
      <StatusBanner status={status} isLoading={statusQuery.isLoading} />

      {/* Fetch button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => fetchMutation.mutate({})}
          disabled={fetchMutation.isPending || !status?.has_refresh_token}
          className={cn(
            'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            status?.has_refresh_token
              ? 'bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          )}
        >
          {fetchMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Pobierz raport EPR
        </button>
        {!status?.has_refresh_token && !statusQuery.isLoading && (
          <span className="text-xs text-gray-500">
            Wymaga autoryzacji Amazon Seller (refresh token)
          </span>
        )}
      </div>

      {/* Reports table */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileBarChart className="h-4 w-4 text-gray-400" />
            Raporty EPR ({reports.length})
          </h3>
        </div>

        {reportsQuery.isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-500" />
          </div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">
            Brak raportów EPR. Kliknij &quot;Pobierz raport EPR&quot; aby pobrać pierwszy raport.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                  <th className="px-5 py-3">Typ</th>
                  <th className="px-5 py-3">Marketplace</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Wiersze</th>
                  <th className="px-5 py-3">Data</th>
                  <th className="px-5 py-3 text-right">Akcje</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <ReportRow
                    key={r.id}
                    report={r}
                    isSelected={selectedId === r.id}
                    onView={() => setSelectedId(selectedId === r.id ? null : r.id)}
                    onDelete={() => {
                      if (!window.confirm('Czy na pewno chcesz usunąć ten raport?')) return
                      if (selectedId === r.id) setSelectedId(null)
                      deleteMutation.mutate(r.id)
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selectedId && (
        <DetailPanel
          report={detail ?? null}
          isLoading={detailQuery.isLoading}
          onClose={() => setSelectedId(null)}
        />
      )}

      {/* Cross-border EPR rules per country */}
      <EprCountryRulesSection />
    </div>
  )
}

function StatusBanner({
  status,
  isLoading,
}: {
  status: { credentials_configured: boolean; has_refresh_token: boolean } | undefined
  isLoading: boolean
}) {
  if (isLoading) {
    return <div className="h-12 animate-pulse rounded-xl border border-gray-800 bg-[#1A1A1A]" />
  }
  if (!status) return null

  const ok = status.credentials_configured && status.has_refresh_token
  return (
    <div className={cn(
      'flex items-center gap-3 rounded-xl border p-4 text-sm',
      ok
        ? 'border-green-500/20 bg-green-500/5 text-green-400'
        : 'border-yellow-500/20 bg-yellow-500/5 text-yellow-400'
    )}>
      {ok ? <CheckCircle className="h-4 w-4 shrink-0" /> : <AlertTriangle className="h-4 w-4 shrink-0" />}
      {ok
        ? 'Połączenie z Amazon SP-API aktywne. Możesz pobierać raporty EPR.'
        : status.credentials_configured
          ? 'Brak refresh token — wymagana autoryzacja Amazon Seller.'
          : 'Brak konfiguracji Amazon SP-API (client_id / client_secret).'}
    </div>
  )
}

function ReportRow({
  report,
  isSelected,
  onView,
  onDelete,
}: {
  report: EprReport
  isSelected: boolean
  onView: () => void
  onDelete: () => void
}) {
  const st = STATUS_STYLES[report.status] ?? { label: report.status, cls: 'bg-gray-500/10 text-gray-400' }

  return (
    <tr className={cn(
      'border-b border-gray-800/50 transition-colors',
      isSelected ? 'bg-white/5' : 'hover:bg-white/[0.02]'
    )}>
      <td className="px-5 py-3 text-gray-300">{report.report_type}</td>
      <td className="px-5 py-3 text-gray-300">{report.marketplace_id}</td>
      <td className="px-5 py-3">
        <span className={cn('rounded px-2 py-0.5 text-xs font-medium', st.cls)}>
          {st.label}
        </span>
      </td>
      <td className="px-5 py-3 text-gray-400">{report.row_count}</td>
      <td className="px-5 py-3 text-gray-500 text-xs">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {new Date(report.created_at).toLocaleString('pl-PL')}
        </span>
      </td>
      <td className="px-5 py-3 text-right">
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={onView}
            className="rounded p-1.5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
            title="Podgląd"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            className="rounded p-1.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
            title="Usuń"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

function DetailPanel({
  report,
  isLoading,
  onClose,
}: {
  report: EprReport | null
  isLoading: boolean
  onClose: () => void
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-white">Szczegóły raportu</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
          <X className="h-4 w-4" />
        </button>
      </div>

      {isLoading ? (
        <div className="p-8 text-center">
          <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-500" />
        </div>
      ) : !report?.rows?.length ? (
        <div className="p-8 text-center text-sm text-gray-500">
          {report?.error_message
            ? `Błąd: ${report.error_message}`
            : 'Brak wierszy danych w tym raporcie.'}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-left text-gray-500">
                <th className="px-4 py-2">ASIN</th>
                <th className="px-4 py-2">Marketplace</th>
                <th className="px-4 py-2">Kategoria EPR</th>
                <th className="px-4 py-2">Szt.</th>
                {MATERIAL_LABELS.map((m) => (
                  <th key={m.key} className="px-4 py-2 text-right">{m.label} (kg)</th>
                ))}
                <th className="px-4 py-2">Okres</th>
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row) => (
                <tr key={row.id} className="border-b border-gray-800/50 hover:bg-white/[0.02]">
                  <td className="px-4 py-2 text-gray-300">{row.asin ?? '—'}</td>
                  <td className="px-4 py-2 text-gray-400">{row.marketplace ?? '—'}</td>
                  <td className="px-4 py-2 text-gray-400">{row.epr_category ?? '—'}</td>
                  <td className="px-4 py-2 text-gray-300">{row.units_sold}</td>
                  {MATERIAL_LABELS.map((m) => (
                    <td key={m.key} className="px-4 py-2 text-right text-gray-400">
                      {row[m.key].toFixed(2)}
                    </td>
                  ))}
                  <td className="px-4 py-2 text-gray-500">{row.reporting_period ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
