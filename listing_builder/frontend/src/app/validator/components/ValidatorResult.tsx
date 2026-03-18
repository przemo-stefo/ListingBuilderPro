// frontend/src/app/validator/components/ValidatorResult.tsx
// Purpose: Display validation result — score gauge, verdict badge, 6 dimension cards
// NOT for: Form input (ValidatorForm.tsx) or history list (ValidatorHistory.tsx)

'use client'

import { CheckCircle2, TrendingUp, AlertTriangle, XCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { ValidatorResponse } from '@/lib/types'

interface ValidatorResultProps {
  result: ValidatorResponse
}

// WHY: Color-code like listing-score — instant visual feedback
function scoreColor(score: number): string {
  if (score >= 8) return 'text-green-400'
  if (score >= 6) return 'text-amber-400'
  return 'text-red-400'
}

function scoreBg(score: number): string {
  if (score >= 8) return 'bg-green-900/20 border-green-800'
  if (score >= 6) return 'bg-amber-900/20 border-amber-800'
  return 'bg-red-900/20 border-red-800'
}

function scoreIcon(score: number) {
  if (score >= 8) return <CheckCircle2 className="h-4 w-4 text-green-400" />
  if (score >= 6) return <TrendingUp className="h-4 w-4 text-amber-400" />
  return <AlertTriangle className="h-4 w-4 text-red-400" />
}

function ScoreBar({ score }: { score: number }) {
  const pct = (score / 10) * 100
  const color = score >= 8 ? 'bg-green-500' : score >= 6 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="h-1.5 w-full rounded-full bg-gray-800">
      <div className={cn('h-1.5 rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
    </div>
  )
}

const VERDICT_CONFIG = {
  warto: { label: 'Warto', icon: CheckCircle2, color: 'text-green-400 bg-green-900/20 border-green-800' },
  ryzykowne: { label: 'Ryzykowne', icon: TrendingUp, color: 'text-amber-400 bg-amber-900/20 border-amber-800' },
  odpusc: { label: 'Odpuść', icon: XCircle, color: 'text-red-400 bg-red-900/20 border-red-800' },
}

export function ValidatorResult({ result }: ValidatorResultProps) {
  const verdict = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.ryzykowne

  return (
    <div className="space-y-4">
      {/* Overall Score + Verdict */}
      <Card className={cn('border', scoreBg(result.score))}>
        <CardContent className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm text-gray-400">Ocena potencjału</p>
            <p className={cn('text-4xl font-bold', scoreColor(result.score))}>
              {result.score}<span className="text-lg text-gray-500">/10</span>
            </p>
          </div>
          <div className="text-right space-y-2">
            <div className={cn('inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5', verdict.color)}>
              <verdict.icon className="h-4 w-4" />
              <span className="text-sm font-semibold">{verdict.label}</span>
            </div>
            <p className="text-xs text-gray-500">
              {result.marketplace} &middot; {result.latency_ms}ms
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Explanation */}
      <Card className="border-gray-800">
        <CardContent className="p-4">
          <p className="text-sm text-gray-300">{result.explanation}</p>
        </CardContent>
      </Card>

      {/* 6 Dimension Cards */}
      {result.dimensions.length > 0 && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {result.dimensions.map((dim, idx) => (
            <Card key={idx} className="border border-gray-800">
              <CardContent className="space-y-3 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {scoreIcon(dim.score)}
                    <span className="text-sm font-medium text-white">{dim.name}</span>
                  </div>
                  <span className={cn('text-lg font-bold', scoreColor(dim.score))}>
                    {dim.score}
                  </span>
                </div>
                <ScoreBar score={dim.score} />
                <p className="text-xs text-gray-400">{dim.comment}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
