// frontend/src/app/optimize/components/ListingScoreCard.tsx
// Purpose: Auto-score card shown after optimization — displays 5-dimension listing quality score
// NOT for: Standalone listing score page (that's /listing-score/page.tsx)

'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { RefreshCw, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react'
import type { ScoreResult } from '@/lib/types'

interface ListingScoreCardProps {
  scoreResult: ScoreResult
  onImprove: () => void
}

// WHY: Reuse same color logic as /listing-score page for consistency
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
  if (score >= 8) return <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
  if (score >= 6) return <TrendingUp className="h-3.5 w-3.5 text-amber-400" />
  return <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
}

export function ListingScoreCard({ scoreResult, onImprove }: ListingScoreCardProps) {
  const { overall_score, dimensions } = scoreResult

  return (
    <Card className={cn('border', scoreBg(overall_score))}>
      <CardContent className="p-6 space-y-4">
        {/* Header: overall score + improve button */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400 mb-1">Ocena listingu</p>
            <p className={cn('text-3xl font-bold', scoreColor(overall_score))}>
              {overall_score.toFixed(1)}<span className="text-sm text-gray-500">/10</span>
            </p>
          </div>
          <div className="text-right space-y-2">
            <p className="text-xs text-gray-500">
              {overall_score >= 8 ? 'Swietny listing!' : overall_score >= 6 ? 'Dobry, ale jest potencjal' : 'Wymaga poprawy'}
            </p>
            {overall_score < 7 && (
              <Button onClick={onImprove} variant="outline" size="sm">
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                Popraw listing
              </Button>
            )}
          </div>
        </div>

        {/* Dimensions grid */}
        {dimensions.length > 0 && (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {dimensions.map((dim, idx) => (
              <div key={idx} className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {scoreIcon(dim.score)}
                    <span className="text-xs font-medium text-white">{dim.name}</span>
                  </div>
                  <span className={cn('text-sm font-bold', scoreColor(dim.score))}>
                    {dim.score}
                  </span>
                </div>
                {/* Progress bar */}
                <div className="h-1 w-full rounded-full bg-gray-800">
                  <div
                    className={cn(
                      'h-1 rounded-full transition-all',
                      dim.score >= 8 ? 'bg-green-500' : dim.score >= 6 ? 'bg-amber-500' : 'bg-red-500'
                    )}
                    style={{ width: `${(dim.score / 10) * 100}%` }}
                  />
                </div>
                {dim.tip && (
                  <p className="text-[10px] text-gray-500 line-clamp-2">{dim.tip}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
