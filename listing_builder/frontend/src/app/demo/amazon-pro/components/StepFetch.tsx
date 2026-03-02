// frontend/src/app/demo/amazon-pro/components/StepFetch.tsx
// Purpose: Step 1 — ASIN input + "Use sample" button → product card + instant TOS scan
// NOT for: Optimization or compliance logic

'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Package, Search, Sparkles, ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react'
import type { DemoProduct, TOSScan, TOSViolation } from '../types'

interface StepFetchProps {
  onComplete: (product: DemoProduct) => void
}

const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

export default function StepFetch({ onComplete }: StepFetchProps) {
  const [asin, setAsin] = useState('')

  const fetchMutation = useMutation({
    mutationFn: async (params: { asin: string; use_sample: boolean }) => {
      const { data } = await apiClient.post('/demo/fetch', params)
      return data
    },
    // WHY no onSuccess→onComplete: Let user review the product card before proceeding.
  })

  const handleFetchSample = () => {
    fetchMutation.mutate({ asin: 'B09EXAMPL1', use_sample: true })
  }

  const handleFetchLive = () => {
    if (asin.length !== 10) return
    fetchMutation.mutate({ asin, use_sample: false })
  }

  const product = fetchMutation.data?.product as DemoProduct | undefined
  const tosScan = fetchMutation.data?.tos_scan as TOSScan | undefined

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Pobierz dane produktu</h2>
        <p className="text-sm text-gray-400">Wpisz ASIN lub użyj przykładowych danych (BIO Spirulina DE)</p>
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

          {product.keywords && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="px-2 py-0.5 bg-green-900/30 text-green-400 rounded">
                {product.keywords.length} keywords
              </span>
              <span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded">
                DataDive RJ scoring
              </span>
            </div>
          )}

          {/* Instant TOS Scan — WOW: shows risks before optimization */}
          {tosScan && <TOSScanPanel scan={tosScan} />}

          <button
            onClick={() => onComplete(product)}
            className="w-full mt-2 px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Dalej — Optymalizuj
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
