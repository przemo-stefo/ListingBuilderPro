// frontend/src/app/compliance/page.tsx
// Purpose: Compliance Guard page — upload marketplace template, view per-product compliance report
// NOT for: API calls or hooks (those are in lib/api/compliance.ts and hooks/useCompliance.ts)

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
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

const MARKETPLACE_OPTIONS = [
  { id: '', label: 'Auto-detect' },
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'kaufland', label: 'Kaufland' },
] as const

type StatusFilter = 'all' | ComplianceItemStatus

export default function CompliancePage() {
  // WHY: null = show upload/list view, string = show report detail view
  const [activeReportId, setActiveReportId] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [marketplace, setMarketplace] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [fileError, setFileError] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  const fileInputRef = useRef<HTMLInputElement>(null)

  // Hooks
  const reportsQuery = useComplianceReports()
  const reportQuery = useComplianceReport(activeReportId)
  const uploadMutation = useUploadCompliance()

  // File validation
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
    if (validateFile(file)) {
      setSelectedFile(file)
    }
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

  // WHY: Score color matches mockup — green 80+, yellow 60-79, red <60
  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const scoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-500/10'
    if (score >= 60) return 'bg-yellow-500/10'
    return 'bg-red-500/10'
  }

  // ──── REPORT DETAIL VIEW ────
  if (activeReportId) {
    const report = reportQuery.data

    return (
      <div className="space-y-6">
        {/* Back button */}
        <button
          onClick={() => { setActiveReportId(null); setStatusFilter('all') }}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Reports
        </button>

        {reportQuery.isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : reportQuery.isError ? (
          <Card>
            <CardContent className="py-10 text-center text-red-400">
              Failed to load report. {reportQuery.error?.message}
            </CardContent>
          </Card>
        ) : report ? (
          <>
            {/* Summary header */}
            <div>
              <h1 className="text-2xl font-bold text-white">{report.filename}</h1>
              <p className="text-sm text-gray-400">
                {report.marketplace} &middot; {report.total_products} products &middot;{' '}
                {new Date(report.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* 4-stat grid */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">Score</p>
                  <p className={cn('text-3xl font-bold', scoreColor(report.overall_score))}>
                    {report.overall_score}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">Compliant</p>
                  <p className="text-3xl font-bold text-green-400">{report.compliant_count}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">Warnings</p>
                  <p className="text-3xl font-bold text-yellow-400">{report.warning_count}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">Errors</p>
                  <p className="text-3xl font-bold text-red-400">{report.error_count}</p>
                </CardContent>
              </Card>
            </div>

            {/* Filter bar */}
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
                  {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                  {f === 'all' && ` (${report.items.length})`}
                  {f === 'error' && ` (${report.error_count})`}
                  {f === 'warning' && ` (${report.warning_count})`}
                  {f === 'compliant' && ` (${report.compliant_count})`}
                </button>
              ))}
            </div>

            {/* Products table with expandable rows */}
            <Card>
              <CardContent className="p-0">
                <div className="divide-y divide-gray-800">
                  {report.items
                    .filter((item) => statusFilter === 'all' || item.status === statusFilter)
                    .map((item) => (
                      <ProductRow key={item.row_number} item={item} />
                    ))}
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    )
  }

  // ──── DEFAULT VIEW: Upload + Past Reports ────
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <Shield className="h-6 w-6 text-green-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">Compliance Guard</h1>
          <p className="text-sm text-gray-400">
            Upload a marketplace template to check for compliance issues
          </p>
        </div>
      </div>

      {/* Upload card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload Template</CardTitle>
          <CardDescription>
            Drop an XLSM, XLSX, or CSV file to analyze compliance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag & drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
              dragOver
                ? 'border-green-500 bg-green-500/5'
                : 'border-gray-700 hover:border-gray-500'
            )}
          >
            <Upload className={cn('h-8 w-8 mb-2', dragOver ? 'text-green-400' : 'text-gray-500')} />
            <p className="text-sm text-gray-400">
              Drag & drop your file here, or <span className="text-white underline">browse</span>
            </p>
            <p className="mt-1 text-xs text-gray-600">XLSM, XLSX, CSV up to 10MB</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileSelect(file)
              e.target.value = '' // WHY: Reset so re-selecting same file triggers onChange
            }}
          />

          {/* File error */}
          {fileError && (
            <p className="text-sm text-red-400">{fileError}</p>
          )}

          {/* Selected file display */}
          {selectedFile && (
            <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-sm text-white">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
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

          {/* Marketplace selector */}
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

          {/* Analyze button */}
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
            Analyze
          </Button>
        </CardContent>
      </Card>

      {/* Past reports table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Past Reports</CardTitle>
          <CardDescription>Click a report to view details</CardDescription>
        </CardHeader>
        <CardContent>
          {reportsQuery.isLoading ? (
            // Loading skeleton
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-gray-800/50" />
              ))}
            </div>
          ) : reportsQuery.isError ? (
            <p className="py-6 text-center text-sm text-red-400">
              Failed to load reports. {reportsQuery.error?.message}
            </p>
          ) : !reportsQuery.data?.items.length ? (
            <p className="py-6 text-center text-sm text-gray-500">
              No reports yet. Upload a template to get started.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Marketplace</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Filename</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Score</th>
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">
                      <span className="text-green-400">OK</span> /{' '}
                      <span className="text-yellow-400">Warn</span> /{' '}
                      <span className="text-red-400">Err</span>
                    </th>
                    <th className="pb-2 text-left font-medium text-gray-400">Date</th>
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
                        <Badge variant="secondary" className="text-[10px]">
                          {r.marketplace}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4 text-white truncate max-w-[200px]">
                        {r.filename}
                      </td>
                      <td className="py-3 pr-4">
                        <span className={cn('font-semibold', scoreColor(r.overall_score))}>
                          {r.overall_score}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-xs">
                        <span className="text-green-400">{r.compliant_count}</span>
                        {' / '}
                        <span className="text-yellow-400">{r.warning_count}</span>
                        {' / '}
                        <span className="text-red-400">{r.error_count}</span>
                      </td>
                      <td className="py-3 text-gray-500 text-xs">
                        {new Date(r.created_at).toLocaleDateString()}
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

// WHY: Separate component for expandable product row — avoids re-rendering the entire list on toggle
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
              {item.issues.length} issue{item.issues.length !== 1 ? 's' : ''}
            </Badge>
          )}
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {expanded && item.issues.length > 0 && (
        <div className="border-t border-gray-800/50 bg-[#121212] px-4 py-3 space-y-2">
          {item.issues.map((issue, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 rounded bg-gray-800/30 px-3 py-2 text-xs"
            >
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
