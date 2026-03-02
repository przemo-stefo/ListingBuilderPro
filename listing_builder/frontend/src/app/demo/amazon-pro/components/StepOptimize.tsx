// frontend/src/app/demo/amazon-pro/components/StepOptimize.tsx
// Purpose: Step 2 — AI optimization with before/after + DataDive RJ coverage
// NOT for: Compliance or publishing logic

'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Sparkles, TrendingUp, BarChart3 } from 'lucide-react'

interface StepOptimizeProps {
  product: any
  onComplete: (optimized: any, coverage: any) => void
}

export default function StepOptimize({ product, onComplete }: StepOptimizeProps) {
  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/demo/optimize', {
        title: product.title,
        brand: product.brand,
        bullets: product.bullets || [],
        description: product.description || '',
        keywords: product.keywords || [],
        marketplace: `amazon_${(product.marketplace || 'de').toLowerCase()}`,
        category: product.category || '',
      })
      return data
    },
    onSuccess: (data) => {
      if (data.optimized && !data.error) {
        onComplete(data.optimized, data.coverage)
      }
    },
  })

  const optimized = mutation.data?.optimized
  const coverage = mutation.data?.coverage

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Optymalizacja AI + DataDive</h2>
        <p className="text-sm text-gray-400">AI optymalizuje listing z Ranking Juice keyword priority</p>
      </div>

      {!optimized && (
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          {mutation.isPending ? 'Optymalizacja w toku (~10-15s)...' : 'Optymalizuj listing'}
        </button>
      )}

      {mutation.error && (
        <p className="text-sm text-red-400">{(mutation.error as any)?.message || 'Błąd optymalizacji'}</p>
      )}

      {optimized && (
        <>
          {/* Coverage Stats */}
          {coverage && (
            <div className="grid grid-cols-3 gap-3">
              <StatBox label="Przed" value={`${coverage.before_pct}%`} color="text-red-400" />
              <StatBox label="Po optymalizacji" value={`${coverage.after_pct}%`} color="text-green-400" />
              <StatBox label="Poprawa" value={`+${coverage.improvement}%`} color="text-blue-400" />
            </div>
          )}

          {/* Before / After Side-by-Side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Before */}
            <div className="border border-gray-800 rounded-xl p-4 bg-[#121212]">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-xs font-medium text-gray-400 uppercase">Przed</span>
              </div>
              <p className="text-sm text-white font-medium mb-2">{product.title}</p>
              {product.bullets?.map((b: string, i: number) => (
                <p key={i} className="text-xs text-gray-500 mb-1">• {b}</p>
              ))}
            </div>

            {/* After */}
            <div className="border border-green-900/50 rounded-xl p-4 bg-green-950/20">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-xs font-medium text-green-400 uppercase">Po optymalizacji</span>
              </div>
              <p className="text-sm text-white font-medium mb-2">{optimized.title}</p>
              {optimized.bullet_points?.map((b: string, i: number) => (
                <p key={i} className="text-xs text-gray-300 mb-1">• {b}</p>
              ))}
            </div>
          </div>

          {/* Ranking Juice Keywords */}
          {product.keywords?.length > 0 && (
            <div className="border border-gray-800 rounded-xl p-4 bg-[#1A1A1A]">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Top Keywords — DataDive Ranking Juice</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                {product.keywords.slice(0, 10).map((kw: any, i: number) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 truncate mr-2">{kw.keyword}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        kw.priority === 'HIGH' ? 'bg-green-900/40 text-green-400' :
                        kw.priority === 'MEDIUM' ? 'bg-yellow-900/40 text-yellow-400' :
                        'bg-gray-800 text-gray-500'
                      }`}>
                        RJ {Math.round(kw.ranking_juice).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => onComplete(optimized, coverage)}
            className="w-full px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Dalej — Sprawdź Compliance
          </button>
        </>
      )}
    </div>
  )
}

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="border border-gray-800 rounded-lg p-3 bg-[#121212] text-center">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
