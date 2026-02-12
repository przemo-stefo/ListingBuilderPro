// frontend/src/app/compliance/components/UploadTab.tsx
// Purpose: File upload + past reports — extracted from original compliance/page.tsx
// NOT for: Dashboard stats, alerts, or integrations (those are separate tabs)

'use client'

import { useState, useCallback, useRef } from 'react'
import {
  Shield,
  Upload,
  Loader2,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  ArrowLeft,
  X,
  FileSpreadsheet,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  useComplianceReports,
  useComplianceReport,
  useUploadCompliance,
} from '@/lib/hooks/useCompliance'
import type { ComplianceItemResult, ComplianceItemStatus } from '@/lib/types'

const ACCEPTED_EXTENSIONS = '.xlsm,.xlsx,.csv'
const MAX_FILE_SIZE = 10 * 1024 * 1024

const MARKETPLACE_OPTIONS = [
  { id: '', label: 'Auto-detect' },
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'kaufland', label: 'Kaufland' },
] as const

type StatusFilter = 'all' | ComplianceItemStatus

export default function UploadTab() {
  const [activeReportId, setActiveReportId] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [marketplace, setMarketplace] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [fileError, setFileError] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const reportsQuery = useComplianceReports()
  const reportQuery = useComplianceReport(activeReportId)
  const uploadMutation = useUploadCompliance()

  const validateFile = (file: File): boolean => {
    setFileError('')
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !['xlsm', 'xlsx', 'csv'].includes(ext)) {
      setFileError('Only .xlsm, .xlsx, and .csv files are accepted.')
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      setFileError(`File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max 10MB.`)
      return false
    }
    return true
  }

  const handleFileSelect = (file: File) => {
    if (validateFile(file)) setSelectedFile(file)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }, [])

  const handleAnalyze = () => {
    if (!selectedFile) return
    uploadMutation.mutate(
      { file: selectedFile, marketplace: marketplace || undefined },
      {
        onSuccess: (data) => {
          setSelectedFile(null)
          setActiveReportId(data.id)
        },
      }
    )
  }

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  // WHY: Report detail view when user clicks into a specific report
  if (activeReportId) {
    const report = reportQuery.data
    return (
      <div className="space-y-6">
        <button
          onClick={() => { setActiveReportId(null); setStatusFilter('all') }}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Wróć do raportów
        </button>

        {reportQuery.isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : reportQuery.isError ? (
          <Card><CardContent className="py-10 text-center text-red-400">
            Nie udało się załadować raportu. {reportQuery.error?.message}
          </CardContent></Card>
        ) : report ? (
          <>
            <div>
              <h2 className="text-xl font-bold text-white">{report.filename}</h2>
              <p className="text-sm text-gray-400">
                {report.marketplace} &middot; {report.total_products} produktów &middot;{' '}
                {new Date(report.created_at).toLocaleDateString('pl-PL')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[
                { label: 'Wynik', value: report.overall_score, color: scoreColor(report.overall_score) },
                { label: 'Zgodne', value: report.compliant_count, color: 'text-green-400' },
                { label: 'Ostrzeżenia', value: report.warning_count, color: 'text-yellow-400' },
                { label: 'Błędy', value: report.error_count, color: 'text-red-400' },
              ].map((s) => (
                <Card key={s.label}><CardContent className="p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">{s.label}</p>
                  <p className={cn('text-3xl font-bold', s.color)}>{s.value}</p>
                </CardContent></Card>
              ))}
            </div>

            <div className="flex gap-2">
              {(['all', 'error', 'warning', 'compliant'] as StatusFilter[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setStatusFilter(f)}
                  className={cn(
                    'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                    statusFilter === f
                      ? 'bg-white text-black'
                      : 'bg-[#1A1A1A] text-gray-400 hover:text-white border border-gray-800'
                  )}
                >
                  {f === 'all' ? `Wszystkie (${report.items.length})` :
                   f === 'error' ? `Błędy (${report.error_count})` :
                   f === 'warning' ? `Ostrzeżenia (${report.warning_count})` :
                   `Zgodne (${report.compliant_count})`}
                </button>
              ))}
            </div>

            <Card><CardContent className="p-0">
              <div className="divide-y divide-gray-800">
                {report.items
                  .filter((item) => statusFilter === 'all' || item.status === statusFilter)
                  .map((item) => <ProductRow key={item.row_number} item={item} />)}
              </div>
            </CardContent></Card>
          </>
        ) : null}
      </div>
    )
  }

  // WHY: Default view — upload zone + past reports table
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Prześlij szablon</CardTitle>
          <CardDescription>Upuść plik XLSM, XLSX lub CSV, aby sprawdzić zgodność</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
              dragOver ? 'border-green-500 bg-green-500/5' : 'border-gray-700 hover:border-gray-500'
            )}
          >
            <Upload className={cn('h-8 w-8 mb-2', dragOver ? 'text-green-400' : 'text-gray-500')} />
            <p className="text-sm text-gray-400">
              Przeciągnij i upuść plik tutaj, lub <span className="text-white underline">wybierz</span>
            </p>
            <p className="mt-1 text-xs text-gray-600">XLSM, XLSX, CSV do 10MB</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileSelect(file)
              e.target.value = ''
            }}
          />

          {fileError && <p className="text-sm text-red-400">{fileError}</p>}

          {selectedFile && (
            <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-sm text-white">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setFileError('') }}
                className="text-gray-500 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <div>
            <p className="mb-2 text-sm text-gray-400">Marketplace</p>
            <div className="flex flex-wrap gap-2">
              {MARKETPLACE_OPTIONS.map((mp) => (
                <button
                  key={mp.id}
                  onClick={() => setMarketplace(mp.id)}
                  className={cn(
                    'rounded-lg border px-4 py-2 text-sm transition-colors',
                    marketplace === mp.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                  )}
                >
                  {mp.label}
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={!selectedFile || uploadMutation.isPending}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {uploadMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Shield className="mr-2 h-4 w-4" />
            )}
            Analizuj
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Historia raportów</CardTitle>
          <CardDescription>Kliknij raport, aby zobaczyć szczegóły</CardDescription>
        </CardHeader>
        <CardContent>
          {reportsQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-gray-800/50" />
              ))}
            </div>
          ) : reportsQuery.isError ? (
            <p className="py-6 text-center text-sm text-red-400">
              Nie udało się załadować raportów. {reportsQuery.error?.message}
            </p>
          ) : !reportsQuery.data?.items.length ? (
            <p className="py-6 text-center text-sm text-gray-500">
              Brak raportów. Prześlij szablon, aby rozpocząć.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Marketplace</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Plik</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Wynik</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">
                      <span className="text-green-400">OK</span> /{' '}
                      <span className="text-yellow-400">Warn</span> /{' '}
                      <span className="text-red-400">Err</span>
                    </th>
                    <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {reportsQuery.data.items.map((r) => (
                    <tr
                      key={r.id}
                      onClick={() => setActiveReportId(r.id)}
                      className="cursor-pointer border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                    >
                      <td className="py-3 pr-4">
                        <Badge variant="secondary" className="text-[10px]">{r.marketplace}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-white truncate max-w-[200px]">{r.filename}</td>
                      <td className="py-3 pr-4">
                        <span className={cn('font-semibold', scoreColor(r.overall_score))}>{r.overall_score}</span>
                      </td>
                      <td className="py-3 pr-4 text-xs">
                        <span className="text-green-400">{r.compliant_count}</span>{' / '}
                        <span className="text-yellow-400">{r.warning_count}</span>{' / '}
                        <span className="text-red-400">{r.error_count}</span>
                      </td>
                      <td className="py-3 text-gray-500 text-xs">
                        {new Date(r.created_at).toLocaleDateString('pl-PL')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// WHY: Separate component — avoids re-rendering entire list on expand toggle
function ProductRow({ item }: { item: ComplianceItemResult }) {
  const [expanded, setExpanded] = useState(false)

  const statusIcon = {
    compliant: <CheckCircle className="h-4 w-4 text-green-400" />,
    warning: <AlertTriangle className="h-4 w-4 text-yellow-400" />,
    error: <XCircle className="h-4 w-4 text-red-400" />,
  }[item.status]

  const severityIcon = {
    error: <XCircle className="h-3 w-3 text-red-400 shrink-0" />,
    warning: <AlertTriangle className="h-3 w-3 text-yellow-400 shrink-0" />,
    info: <Info className="h-3 w-3 text-blue-400 shrink-0" />,
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          {statusIcon}
          <span className="text-xs text-gray-500 w-8">#{item.row_number}</span>
          <span className="text-xs text-gray-400 font-mono w-24 truncate">{item.sku}</span>
          <span className="text-sm text-white truncate max-w-xs">{item.product_title}</span>
        </div>
        <div className="flex items-center gap-2">
          {item.issues.length > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {item.issues.length} {item.issues.length === 1 ? 'problem' : 'problemów'}
            </Badge>
          )}
          {expanded ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
        </div>
      </button>
      {expanded && item.issues.length > 0 && (
        <div className="border-t border-gray-800/50 bg-[#121212] px-4 py-3 space-y-2">
          {item.issues.map((issue, idx) => (
            <div key={idx} className="flex items-start gap-2 rounded bg-gray-800/30 px-3 py-2 text-xs">
              {severityIcon[issue.severity]}
              <div>
                <span className="font-mono text-gray-400">{issue.field}</span>
                <span className="text-gray-600 mx-1">&middot;</span>
                <span className="text-gray-300">{issue.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
