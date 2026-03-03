// frontend/src/app/demo/amazon-pro/components/StepFetch.tsx
// Purpose: Step 1 — ASIN input + CSV upload (Helium10/DataDive) + sample → product card + TOS scan
// NOT for: Optimization or compliance logic

'use client'

import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Package, Search, Sparkles, ShieldAlert, ShieldCheck, AlertTriangle, Upload, FileText, X } from 'lucide-react'
import type { DemoProduct, TOSScan, TOSViolation, KeywordUploadResult, ParsedKeyword } from '../types'

interface StepFetchProps {
  onComplete: (product: DemoProduct) => void
}

const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

// WHY: Map source names to friendly display labels
const SOURCE_LABELS: Record<string, string> = {
  datadive: 'DataDive',
  cerebro: 'Helium10 Cerebro',
  magnet: 'Helium10 Magnet',
  blackbox: 'Helium10 BlackBox',
  generic: 'CSV',
}

export default function StepFetch({ onComplete }: StepFetchProps) {
  const [asin, setAsin] = useState('')
  const [uploadedKeywords, setUploadedKeywords] = useState<KeywordUploadResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchMutation = useMutation({
    mutationFn: async (params: { asin: string; use_sample: boolean }) => {
      const { data } = await apiClient.post('/demo/fetch', params)
      return data
    },
  })

  // WHY: File upload for Helium10/DataDive CSV
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await apiClient.post('/demo/upload-keywords', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data as KeywordUploadResult
    },
    onSuccess: (data) => {
      if (data.error) return
      setUploadedKeywords(data)
    },
  })

  const handleFetchSample = () => {
    fetchMutation.mutate({ asin: 'B09EXAMPL1', use_sample: true })
  }

  const handleFetchLive = () => {
    if (asin.length !== 10) return
    fetchMutation.mutate({ asin, use_sample: false })
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    uploadMutation.mutate(file)
    // WHY: Reset input so same file can be re-uploaded
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleClearKeywords = () => {
    setUploadedKeywords(null)
  }

  // WHY: Merge uploaded keywords into product data when proceeding
  const handleProceed = () => {
    if (!product) return
    if (uploadedKeywords && uploadedKeywords.keywords.length > 0) {
      // WHY: Convert ParsedKeyword → DemoKeyword format expected by StepOptimize
      const mergedKeywords = uploadedKeywords.keywords.slice(0, 200).map((k: ParsedKeyword) => ({
        keyword: k.phrase,
        search_volume: k.search_volume,
        relevance: k.relevancy,
        competition: k.competition,
        ranking_juice: k.ranking_juice,
        priority: (k.ranking_juice > 5000 ? 'HIGH' : k.ranking_juice > 1000 ? 'MEDIUM' : 'LOW') as 'HIGH' | 'MEDIUM' | 'LOW',
      }))
      onComplete({ ...product, keywords: mergedKeywords })
    } else {
      onComplete(product)
    }
  }

  const product = fetchMutation.data?.product as DemoProduct | undefined
  const tosScan = fetchMutation.data?.tos_scan as TOSScan | undefined

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Krok 1: Pobierz dane produktu</h2>
        <p className="text-sm text-gray-400">Wpisz ASIN lub użyj przykładu. Opcjonalnie zaimportuj keywords z Helium10/DataDive.</p>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={asin}
          onChange={(e) => setAsin(e.target.value.toUpperCase())}
          placeholder="Wpisz ASIN (np. B09EXAMPL1)"
          className={inputCls}
          maxLength={10}
        />
        <button
          onClick={handleFetchLive}
          disabled={asin.length !== 10 || fetchMutation.isPending}
          className="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-medium hover:bg-white/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
        >
          <Search className="w-4 h-4" />
          Szukaj
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-800" />
        <span className="text-xs text-gray-600">lub</span>
        <div className="flex-1 h-px bg-gray-800" />
      </div>

      <button
        onClick={handleFetchSample}
        disabled={fetchMutation.isPending}
        className="w-full px-4 py-3 bg-blue-600/20 border border-blue-600/30 text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-600/30 disabled:opacity-40 flex items-center justify-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        {fetchMutation.isPending ? 'Pobieranie...' : 'Użyj przykładu — BIO Spirulina 500mg'}
      </button>

      {/* CSV Upload Section */}
      <div className="border border-gray-800 rounded-xl p-4 bg-[#121212] space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-300">Import keywords z Helium10 / DataDive</span>
          <span className="text-[10px] text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">opcjonalnie</span>
        </div>

        {!uploadedKeywords ? (
          <div className="space-y-2">
            <p className="text-xs text-gray-500">
              Eksportuj CSV z Cerebro, Magnet lub DataDive → upload tutaj. System automatycznie rozpozna format i wyciągnie keywords z search volume + Ranking Juice.
            </p>
            <div className="flex gap-2">
              <label className="flex-1 cursor-pointer">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.tsv,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <div className="flex items-center justify-center gap-2 px-4 py-2.5 border border-dashed border-gray-700 rounded-lg text-sm text-gray-400 hover:border-gray-500 hover:text-white transition-colors">
                  <Upload className="w-4 h-4" />
                  {uploadMutation.isPending ? 'Parsowanie...' : 'Upload CSV'}
                </div>
              </label>
            </div>
            {uploadMutation.error && (
              <p className="text-xs text-red-400">{(uploadMutation.error as Error)?.message || 'Błąd parsowania CSV'}</p>
            )}
            {uploadMutation.data?.error && (
              <p className="text-xs text-red-400">{uploadMutation.data.error}</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded text-xs font-medium">
                  {SOURCE_LABELS[uploadedKeywords.source] || uploadedKeywords.source}
                </span>
                <span className="text-xs text-gray-400">
                  {uploadedKeywords.stats.total} keywords
                </span>
                {uploadedKeywords.stats.with_volume > 0 && (
                  <span className="text-xs text-gray-500">
                    · avg vol: {uploadedKeywords.stats.avg_volume.toLocaleString()}
                  </span>
                )}
                {uploadedKeywords.stats.top_rj && uploadedKeywords.stats.top_rj > 0 && (
                  <span className="text-xs text-gray-500">
                    · top RJ: {uploadedKeywords.stats.top_rj.toLocaleString()}
                  </span>
                )}
              </div>
              <button onClick={handleClearKeywords} className="text-gray-600 hover:text-gray-400">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Top 5 keywords preview */}
            <div className="space-y-1">
              {uploadedKeywords.keywords.slice(0, 5).map((kw, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-gray-300 truncate mr-2">{kw.phrase}</span>
                  <div className="flex items-center gap-3 shrink-0 text-gray-500">
                    <span>vol: {kw.search_volume.toLocaleString()}</span>
                    <span>RJ: {kw.ranking_juice.toLocaleString()}</span>
                    {kw.relevancy > 0 && <span>rel: {kw.relevancy}</span>}
                  </div>
                </div>
              ))}
              {uploadedKeywords.keywords.length > 5 && (
                <p className="text-[10px] text-gray-600">
                  + {uploadedKeywords.keywords.length - 5} więcej keywords...
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {fetchMutation.error && (
        <p className="text-sm text-red-400">{(fetchMutation.error as Error)?.message || 'Błąd pobierania'}</p>
      )}

      {/* Product Card */}
      {product && (
        <div className="border border-gray-800 rounded-xl p-4 bg-[#1A1A1A] space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-16 h-16 bg-gray-800 rounded-lg flex items-center justify-center shrink-0">
              <Package className="w-8 h-8 text-gray-600" />
            </div>
            <div className="min-w-0">
              <p className="text-white font-medium text-sm leading-tight">{product.title}</p>
              <p className="text-gray-500 text-xs mt-1">{product.brand} · {product.asin} · Amazon {product.marketplace}</p>
            </div>
          </div>

          {product.bullets?.length > 0 && (
            <div className="space-y-1">
              {product.bullets.slice(0, 3).map((b: string, i: number) => (
                <p key={i} className="text-xs text-gray-400 truncate">• {b}</p>
              ))}
              {product.bullets.length > 3 && (
                <p className="text-xs text-gray-600">+ {product.bullets.length - 3} więcej...</p>
              )}
            </div>
          )}

          {/* Keywords badge — show uploaded OR sample keywords */}
          <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
            {uploadedKeywords ? (
              <>
                <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded">
                  {uploadedKeywords.stats.total} keywords ({SOURCE_LABELS[uploadedKeywords.source]})
                </span>
                <span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded">
                  real search volume data
                </span>
              </>
            ) : product.keywords ? (
              <>
                <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded">
                  {product.keywords.length} keywords
                </span>
                <span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded">
                  DataDive RJ scoring
                </span>
              </>
            ) : null}
          </div>

          {/* Instant TOS Scan */}
          {tosScan && <TOSScanPanel scan={tosScan} />}

          <button
            onClick={handleProceed}
            className="w-full mt-2 px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Przejdź do kroku 2: Optymalizacja AI
          </button>
        </div>
      )}
    </div>
  )
}

function TOSScanPanel({ scan }: { scan: TOSScan }) {
  if (scan.severity === 'PASS') {
    return (
      <div className="flex items-center gap-2 border border-green-900/40 bg-green-950/20 rounded-lg px-3 py-2">
        <ShieldCheck className="w-4 h-4 text-green-400 shrink-0" />
        <span className="text-xs text-green-400">Amazon TOS — Brak naruszeń wykrytych</span>
      </div>
    )
  }

  return (
    <div className="border border-red-900/40 bg-red-950/10 rounded-lg p-3 space-y-2">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
        <span className="text-xs font-medium text-red-400">
          Amazon TOS Scan — {scan.violation_count} {scan.violation_count === 1 ? 'ryzyko' : 'ryzyk'} wykryte
        </span>
        {scan.suppression_risk && (
          <span className="text-[10px] bg-red-900/40 text-red-300 px-1.5 py-0.5 rounded font-medium">
            SUPPRESSION RISK
          </span>
        )}
      </div>
      {scan.violations.slice(0, 3).map((v: TOSViolation, i: number) => (
        <div key={i} className="flex items-start gap-2 text-xs">
          <AlertTriangle className={`w-3 h-3 shrink-0 mt-0.5 ${
            v.severity === 'SUPPRESSION' ? 'text-red-400' : 'text-yellow-400'
          }`} />
          <span className="text-gray-400">{v.message}</span>
        </div>
      ))}
      {scan.violations.length > 3 && (
        <p className="text-[10px] text-gray-600 pl-5">+ {scan.violations.length - 3} więcej...</p>
      )}
    </div>
  )
}
