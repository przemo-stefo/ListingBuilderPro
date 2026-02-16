// frontend/src/app/optimize/components/RankingJuiceCard.tsx
// Purpose: Ranking Juice score display with component breakdown (premium)
// NOT for: Other result display components

'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Lock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import type { RankingJuice } from '@/lib/types'

// WHY: Ranking Juice = quantifiable metric for listing quality (0-100, ported from AmazonListingMaster)
export function RankingJuiceCard({
  rankingJuice,
  optimizationSource,
}: {
  rankingJuice: RankingJuice
  optimizationSource?: string
}) {
  const [expanded, setExpanded] = useState(false)
  const { isPremium } = useTier()

  const gradeColor =
    rankingJuice.grade === 'A+' || rankingJuice.grade === 'A'
      ? 'text-green-400'
      : rankingJuice.grade === 'B'
        ? 'text-blue-400'
        : rankingJuice.grade === 'C'
          ? 'text-yellow-400'
          : 'text-red-400'

  const gradeBg =
    rankingJuice.grade === 'A+' || rankingJuice.grade === 'A'
      ? 'bg-green-500/10 border-green-500/30'
      : rankingJuice.grade === 'B'
        ? 'bg-blue-500/10 border-blue-500/30'
        : rankingJuice.grade === 'C'
          ? 'bg-yellow-500/10 border-yellow-500/30'
          : 'bg-red-500/10 border-red-500/30'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-lg">Ranking Juice</CardTitle>
            {optimizationSource && (
              <Badge
                variant="secondary"
                className={cn(
                  'text-[10px]',
                  optimizationSource === 'n8n'
                    ? 'bg-blue-500/10 text-blue-400'
                    : 'bg-gray-500/10 text-gray-400'
                )}
              >
                {optimizationSource === 'n8n' ? 'n8n' : 'direct'}
              </Badge>
            )}
          </div>
          <div className={cn('flex items-center gap-2 rounded-lg border px-4 py-2', gradeBg)}>
            <span className={cn('text-3xl font-bold', gradeColor)}>
              {rankingJuice.score}
            </span>
            <div className="flex flex-col">
              <span className={cn('text-lg font-bold leading-tight', gradeColor)}>
                {rankingJuice.grade}
              </span>
              <span className="text-[10px] text-gray-500">/100</span>
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-400">{rankingJuice.verdict}</p>
      </CardHeader>
      <CardContent>
        {isPremium ? (
          <>
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
            >
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              Rozklad komponentow
            </button>
            {expanded && (
              <div className="mt-3 space-y-2">
                {Object.entries(rankingJuice.components).map(([key, value]) => {
                  const weight = rankingJuice.weights[key] || 0
                  const contribution = value * weight
                  const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                  const barWidth = Math.min(100, value)
                  return (
                    <div key={key} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400">{label}</span>
                        <span className="text-gray-500">
                          {value}/100 (x{weight} = {contribution.toFixed(1)})
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-gray-800">
                        <div
                          className={cn(
                            'h-1.5 rounded-full transition-all',
                            value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          )}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Lock className="h-3 w-3 text-amber-400" />
            <span>Pelny breakdown dostepny w Premium</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
