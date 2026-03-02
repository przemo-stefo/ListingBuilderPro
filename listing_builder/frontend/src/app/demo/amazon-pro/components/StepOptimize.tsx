// frontend/src/app/demo/amazon-pro/components/StepOptimize.tsx
// Purpose: Step 2 — AI optimization with before/after + DataDive RJ coverage + Listing DNA
// NOT for: Compliance or publishing logic

'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Sparkles, BarChart3, Dna, ShieldCheck, ShieldAlert, TrendingUp } from 'lucide-react'
import type { DemoProduct, DemoKeyword, OptimizedListing, CoverageResult, ListingDNA } from '../types'

interface StepOptimizeProps {
  product: DemoProduct
  onComplete: (optimized: OptimizedListing, coverage: CoverageResult) => void
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
    // WHY no onSuccess→onComplete: User must SEE the Listing DNA + results before
    // clicking "Dalej". Auto-advance would unmount the component instantly.
  })

  const optimized = mutation.data?.optimized as OptimizedListing | undefined
  const coverage = mutation.data?.coverage as CoverageResult | undefined
  const listingDna = mutation.data?.listing_dna as ListingDNA | undefined

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
        <p className="text-sm text-red-400">{(mutation.error as Error)?.message || 'Błąd optymalizacji'}</p>
      )}

      {optimized && (
        <>
          {/* === LISTING DNA — The WOW Feature === */}
          {listingDna && <ListingDNAPanel dna={listingDna} />}

          {/* Coverage Stats */}
          {coverage && (
            <div className="grid grid-cols-3 gap-3">
              <StatBox label="Pokrycie (przed)" value={`${coverage.before_pct}%`} color="text-red-400" />
              <StatBox label="Pokrycie (po)" value={`${coverage.after_pct}%`} color="text-green-400" />
              <StatBox label="Poprawa" value={`+${coverage.improvement}%`} color="text-blue-400" />
            </div>
          )}

          {/* Before / After Side-by-Side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
          {(product.keywords?.length ?? 0) > 0 && (
            <div className="border border-gray-800 rounded-xl p-4 bg-[#1A1A1A]">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Top Keywords — DataDive Ranking Juice</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                {product.keywords!.slice(0, 10).map((kw: DemoKeyword, i: number) => (
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
            onClick={() => onComplete(optimized, coverage!)}
            className="w-full px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Dalej — Sprawdź Compliance
          </button>
        </>
      )}
    </div>
  )
}

// --- Listing DNA Panel ---

const COMPONENT_LABELS: Record<string, string> = {
  keyword_coverage: 'Pokrycie keywords',
  exact_match_density: 'Exact match',
  search_volume_weighted: 'Search volume',
  backend_efficiency: 'Backend keywords',
  structure_quality: 'Struktura listingu',
}

function gradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'text-green-400 border-green-500'
  if (grade === 'B') return 'text-blue-400 border-blue-500'
  if (grade === 'C') return 'text-yellow-400 border-yellow-500'
  return 'text-red-400 border-red-500'
}

function barColor(value: number): string {
  if (value >= 80) return 'bg-green-500'
  if (value >= 60) return 'bg-blue-500'
  if (value >= 40) return 'bg-yellow-500'
  return 'bg-red-500'
}

function ListingDNAPanel({ dna }: { dna: ListingDNA }) {
  const { before, after } = dna

  return (
    <div className="border border-gray-700 rounded-xl p-5 bg-gradient-to-br from-[#121212] to-[#1A1A2E]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Dna className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-bold text-white tracking-wide">LISTING DNA</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <TrendingUp className="w-3.5 h-3.5 text-green-400" />
          <span className="text-green-400 font-medium">+{dna.improvement} pkt</span>
        </div>
      </div>

      {/* Grade Badges — Before vs After */}
      <div className="grid grid-cols-2 gap-4 mb-5">
        <div className="flex items-center gap-3">
          <div className={`w-14 h-14 rounded-full flex items-center justify-center border-2 ${gradeColor(before.grade)}`}>
            <span className="text-lg font-black">{before.grade}</span>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Przed</p>
            <p className="text-white font-bold text-lg">{before.score}/100</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className={`w-14 h-14 rounded-full flex items-center justify-center border-2 ${gradeColor(after.grade)}`}>
            <span className="text-lg font-black">{after.grade}</span>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Po optymalizacji</p>
            <p className="text-white font-bold text-lg">{after.score}/100</p>
          </div>
        </div>
      </div>

      {/* Component Bars */}
      <div className="space-y-2.5 mb-4">
        {Object.entries(COMPONENT_LABELS).map(([key, label]) => {
          const beforeVal = before.components[key as keyof typeof before.components] ?? 0
          const afterVal = after.components[key as keyof typeof after.components] ?? 0
          const delta = Math.round(afterVal - beforeVal)
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] text-gray-400">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-600">{Math.round(beforeVal)}</span>
                  <span className="text-[10px] text-gray-500">→</span>
                  <span className="text-[10px] text-white font-medium">{Math.round(afterVal)}</span>
                  {delta > 0 && (
                    <span className="text-[9px] text-green-400 font-medium">+{delta}</span>
                  )}
                </div>
              </div>
              <div className="flex gap-1 h-1.5">
                {/* Before bar (dimmed) */}
                <div className="flex-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gray-600 rounded-full transition-all"
                    style={{ width: `${Math.min(100, beforeVal)}%` }}
                  />
                </div>
                {/* After bar (colored) */}
                <div className="flex-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(afterVal)}`}
                    style={{ width: `${Math.min(100, afterVal)}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* TOS Status */}
      <div className="flex items-center justify-between border-t border-gray-800 pt-3">
        <div className="flex items-center gap-2">
          {after.suppression_risk ? (
            <ShieldAlert className="w-4 h-4 text-red-400" />
          ) : (
            <ShieldCheck className="w-4 h-4 text-green-400" />
          )}
          <span className="text-xs text-gray-400">Amazon TOS</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {before.tos_violations > 0 ? (
            <span className="text-red-400">{before.tos_violations} naruszeń</span>
          ) : (
            <span className="text-green-400">OK</span>
          )}
          <span className="text-gray-600">→</span>
          {after.tos_violations > 0 ? (
            <span className="text-red-400">{after.tos_violations} naruszeń</span>
          ) : (
            <span className="text-green-400">0 naruszeń</span>
          )}
          {dna.tos_issues_fixed > 0 && (
            <span className="text-green-400 bg-green-900/30 px-1.5 py-0.5 rounded text-[10px] font-medium">
              -{dna.tos_issues_fixed} naprawione
            </span>
          )}
        </div>
      </div>

      {/* Suppression Risk */}
      {before.suppression_risk && !after.suppression_risk && (
        <div className="mt-2 flex items-center gap-2 text-[11px] bg-green-900/20 border border-green-900/40 rounded-lg px-3 py-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-green-400" />
          <span className="text-green-400">Ryzyko suppression wyeliminowane</span>
        </div>
      )}
    </div>
  )
}

// --- Shared Components ---

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="border border-gray-800 rounded-lg p-3 bg-[#121212] text-center">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
