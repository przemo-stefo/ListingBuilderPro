// frontend/src/app/demo/amazon-pro/components/StepCompliance.tsx
// Purpose: Step 3 — EU supplement compliance check results
// NOT for: Compliance Guard (XLSM) or general compliance features

'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Shield, AlertTriangle, CheckCircle, XCircle, FlaskConical, Copy, Check } from 'lucide-react'
import type { DemoProduct, OptimizedListing, ComplianceResult, ComplianceIssue, EFSAClaimsResult, EFSAIngredientResult } from '../types'

interface StepComplianceProps {
  optimized: OptimizedListing | null
  product: DemoProduct
  onComplete: (complianceResult: ComplianceResult) => void
}

export default function StepCompliance({ optimized, product, onComplete }: StepComplianceProps) {
  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/demo/compliance-check', {
        title: optimized?.title || product.title,
        bullets: optimized?.bullet_points || product.bullets || [],
        description: optimized?.description || product.description || '',
        manufacturer: product.manufacturer || '',
        category: product.category || '',
      })
      return data
    },
    // WHY no onSuccess→onComplete: User must see compliance results before proceeding.
  })

  const result = mutation.data

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Krok 3: Sprawdzenie zgodności z EU</h2>
        <p className="text-sm text-gray-400">Automatycznie sprawdzamy Twój listing pod kątem regulacji EU dla suplementów — niedozwolone health claims, GPSR, alergeny.</p>
      </div>

      {!result && (
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 flex items-center justify-center gap-2"
        >
          <Shield className="w-4 h-4" />
          {mutation.isPending ? 'Sprawdzanie...' : 'Sprawdź compliance'}
        </button>
      )}

      {result && (
        <>
          {/* Score Badge */}
          <div className="flex items-center gap-4">
            <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 ${
              result.status === 'PASS' ? 'border-green-500 text-green-400' :
              result.status === 'WARNING' ? 'border-yellow-500 text-yellow-400' :
              'border-red-500 text-red-400'
            }`}>
              <span className="text-2xl font-bold">{result.score}</span>
            </div>
            <div>
              <p className={`text-lg font-semibold ${
                result.status === 'PASS' ? 'text-green-400' :
                result.status === 'WARNING' ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {result.status === 'PASS' ? 'Zgodny' : result.status === 'WARNING' ? 'Ostrzeżenia' : 'Niezgodny'}
              </p>
              <p className="text-sm text-gray-400">
                {result.summary?.fail_count} błędów · {result.summary?.warning_count} ostrzeżeń · {result.checks_run} testów
              </p>
            </div>
          </div>

          {/* Issues List */}
          {result.issues?.length > 0 && (
            <div className="space-y-2">
              {result.issues.map((issue: ComplianceIssue, i: number) => (
                <div
                  key={i}
                  className={`border rounded-lg p-3 ${
                    issue.severity === 'FAIL'
                      ? 'border-red-900/50 bg-red-950/20'
                      : 'border-yellow-900/50 bg-yellow-950/20'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {issue.severity === 'FAIL' ? (
                      <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-sm text-white">{issue.message}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                          {issue.field}
                        </span>
                        <span className="text-[10px] text-gray-500">{issue.regulation}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.issues?.length === 0 && (
            <div className="flex items-center gap-2 text-green-400 border border-green-900/50 rounded-lg p-3 bg-green-950/20">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm">Wszystkie testy przeszły pomyślnie</span>
            </div>
          )}

          {/* === WOW Feature 2: EFSA Ingredient-to-Claims Mapper === */}
          <EFSAClaimsPanel product={product} optimized={optimized} />

          <button
            onClick={() => onComplete(result)}
            className="w-full px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Przejdź do kroku 4: Publikacja na Amazon
          </button>
        </>
      )}
    </div>
  )
}


// --- WOW Feature 2: EFSA Ingredient-to-Claims Mapper ---

function EFSAClaimsPanel({ product, optimized }: { product: DemoProduct; optimized: OptimizedListing | null }) {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/demo/ingredient-claims', {
        ingredients: [],  // WHY: empty = auto-detect from title/bullets
        current_bullets: optimized?.bullet_points || product.bullets || [],
        title: optimized?.title || product.title,
      })
      return data as EFSAClaimsResult
    },
  })

  const result = mutation.data

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text)
    setCopiedIdx(idx)
    setTimeout(() => setCopiedIdx(null), 2000)
  }

  return (
    <div className="border border-gray-700 rounded-xl p-5 bg-gradient-to-br from-[#121212] to-[#1A1A1A]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FlaskConical className="w-5 h-5 text-emerald-400" />
          <span className="text-sm font-bold text-white tracking-wide">EFSA CLAIMS ASSISTANT</span>
        </div>
        <span className="text-[10px] text-gray-600 bg-gray-800 px-2 py-0.5 rounded">EU REGISTER</span>
      </div>

      {!result && (
        <>
          <p className="text-xs text-gray-400 mb-3">
            Automatycznie mapuje składniki suplementu na legalne EU health claims z rejestru EFSA. Pokazuje co jest dozwolone, a co zabronione.
          </p>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="w-full px-3 py-2 bg-emerald-600/20 border border-emerald-900/50 text-emerald-400 rounded-lg text-xs font-semibold hover:bg-emerald-600/30 disabled:opacity-40 flex items-center justify-center gap-2"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            {mutation.isPending ? 'Analizowanie składników...' : 'Mapuj składniki na EFSA claims'}
          </button>
        </>
      )}

      {result && !result.error && (
        <div className="space-y-3">
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center bg-[#0D0D0D] rounded-lg p-2">
              <p className="text-lg font-bold text-white">{result.summary.total_ingredients}</p>
              <p className="text-[9px] text-gray-500">Składników</p>
            </div>
            <div className="text-center bg-[#0D0D0D] rounded-lg p-2">
              <p className="text-lg font-bold text-emerald-400">{result.summary.approved_claims_available}</p>
              <p className="text-[9px] text-gray-500">EFSA claims</p>
            </div>
            <div className="text-center bg-[#0D0D0D] rounded-lg p-2">
              <p className="text-lg font-bold text-red-400">{result.summary.forbidden_claims_found}</p>
              <p className="text-[9px] text-gray-500">Zabronione</p>
            </div>
          </div>

          {result.auto_detected && (
            <p className="text-[10px] text-gray-500 bg-gray-800/50 rounded px-2 py-1">
              Składniki wykryte automatycznie z tytułu i bullets
            </p>
          )}

          {/* Ingredient cards */}
          <div className="space-y-2">
            {result.ingredients.filter((ing: EFSAIngredientResult) => ing.found).map((ing: EFSAIngredientResult, i: number) => (
              <div key={i} className="bg-[#0D0D0D] rounded-lg p-3 border border-gray-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-white capitalize">{ing.name}</span>
                  {ing.forbidden_in_listing.length > 0 ? (
                    <span className="text-[9px] bg-red-900/40 text-red-400 px-1.5 py-0.5 rounded font-medium">
                      {ing.forbidden_in_listing.length} FORBIDDEN
                    </span>
                  ) : (
                    <span className="text-[9px] bg-emerald-900/40 text-emerald-400 px-1.5 py-0.5 rounded font-medium">
                      COMPLIANT
                    </span>
                  )}
                </div>

                {/* Forbidden claims found in listing */}
                {ing.forbidden_in_listing.length > 0 && (
                  <div className="mb-2 space-y-1">
                    {ing.forbidden_in_listing.map((f, fi) => (
                      <div key={fi} className="flex items-center gap-1.5 text-[11px]">
                        <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                        <span className="text-red-300">In listing: &quot;{f.matched_text}&quot;</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* EFSA approved claims (DE) */}
                <div className="space-y-1">
                  {ing.approved_claims.de.slice(0, 3).map((claim, ci) => (
                    <div key={ci} className="flex items-center gap-1.5 group">
                      <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                      <span className="text-[11px] text-gray-300 flex-1">{claim}</span>
                      <button
                        onClick={() => handleCopy(claim, i * 10 + ci)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy claim"
                      >
                        {copiedIdx === i * 10 + ci ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Copy className="w-3 h-3 text-gray-600 hover:text-gray-400" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>

                {/* Suggestion */}
                {ing.forbidden_in_listing.length > 0 && ing.suggestion && (
                  <p className="text-[10px] text-yellow-400 mt-1.5 bg-yellow-950/20 rounded px-2 py-1">
                    {ing.suggestion}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-lg p-2.5 text-center">
            <p className="text-[11px] text-emerald-400 font-medium">
              Pełna baza EFSA: 50+ składników × legalne claims DE/EN — copy &amp; paste do listingu.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
