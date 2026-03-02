// frontend/src/app/demo/amazon-pro/components/StepCompliance.tsx
// Purpose: Step 3 — EU supplement compliance check results
// NOT for: Compliance Guard (XLSM) or general compliance features

'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Shield, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

interface StepComplianceProps {
  optimized: any
  product: any
  onComplete: (complianceResult: any) => void
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
    onSuccess: (data) => {
      onComplete(data)
    },
  })

  const result = mutation.data

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">EU Compliance Check</h2>
        <p className="text-sm text-gray-400">Regulacje: HCPR (EC 1924/2006), GPSR, FIC 1169/2011, Amazon Policy</p>
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
              {result.issues.map((issue: any, i: number) => (
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

          <button
            onClick={() => onComplete(result)}
            className="w-full px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Dalej — Opublikuj na Amazon
          </button>
        </>
      )}
    </div>
  )
}
