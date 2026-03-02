// frontend/src/app/demo/amazon-pro/components/StepFetch.tsx
// Purpose: Step 1 — ASIN input + "Use sample" button → product card
// NOT for: Optimization or compliance logic

'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Package, Search, Sparkles } from 'lucide-react'

interface StepFetchProps {
  onComplete: (product: any) => void
}

const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

export default function StepFetch({ onComplete }: StepFetchProps) {
  const [asin, setAsin] = useState('')

  const fetchMutation = useMutation({
    mutationFn: async (params: { asin: string; use_sample: boolean }) => {
      const { data } = await apiClient.post('/demo/fetch', params)
      return data
    },
    onSuccess: (data) => {
      if (data.product) onComplete(data.product)
    },
  })

  const handleFetchSample = () => {
    fetchMutation.mutate({ asin: 'B09EXAMPLE1', use_sample: true })
  }

  const handleFetchLive = () => {
    if (asin.length !== 10) return
    fetchMutation.mutate({ asin, use_sample: false })
  }

  const product = fetchMutation.data?.product

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
          placeholder="Wpisz ASIN (np. B09EXAMPLE1)"
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
        <p className="text-sm text-red-400">{(fetchMutation.error as any)?.message || 'Błąd pobierania'}</p>
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
