// frontend/src/app/optimize/components/PPCRecommendationsCard.tsx
// Purpose: Display PPC match-type recommendations — premium-gated
// NOT for: PPC campaign management or bid changes

'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Lock, Target, Crosshair, Globe, Ban } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import type { PPCRecommendations, PPCRecommendation } from '@/lib/types'

function MatchSection({
  title,
  icon: Icon,
  items,
  color,
}: {
  title: string
  icon: React.ElementType
  items: PPCRecommendation[]
  color: string
}) {
  if (items.length === 0) return null
  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        <Icon className={cn('h-4 w-4', color)} />
        <h4 className="text-sm font-medium text-gray-300">{title}</h4>
        <Badge variant="secondary" className="text-[10px]">{items.length}</Badge>
      </div>
      <div className="space-y-1">
        {items.map((kw, i) => (
          <div key={i} className="flex items-center justify-between rounded border border-gray-800 bg-[#1A1A1A] px-3 py-1.5 text-xs">
            <span className="text-white">{kw.phrase}</span>
            <div className="flex items-center gap-2">
              {kw.search_volume > 0 && (
                <span className="text-gray-500">{kw.search_volume.toLocaleString()} vol</span>
              )}
              {kw.indexed && (
                <Badge variant="secondary" className="bg-green-500/10 text-[9px] text-green-400">indexed</Badge>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function PPCRecommendationsCard({ ppc }: { ppc: PPCRecommendations }) {
  const { isPremium } = useTier()
  const [expanded, setExpanded] = useState(false)

  if (!isPremium) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-gray-400" />
              <CardTitle className="text-lg">PPC Rekomendacje</CardTitle>
            </div>
            <div className="flex items-center gap-1 text-xs text-amber-400">
              <Lock className="h-3 w-3" />
              Premium
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Rekomendacje match-type dla kampanii PPC dostepne w planie Premium.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <button onClick={() => setExpanded(!expanded)} className="flex w-full items-center justify-between p-6">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">PPC Rekomendacje</h3>
          <Badge variant="secondary" className="text-[10px]">
            {ppc.summary.exact_count + ppc.summary.phrase_count + ppc.summary.broad_count} slow
          </Badge>
        </div>
        {expanded ? <ChevronDown className="h-5 w-5 text-gray-400" /> : <ChevronRight className="h-5 w-5 text-gray-400" />}
      </button>
      {expanded && (
        <CardContent className="space-y-4 pt-0">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div className="rounded border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-lg font-bold text-green-400">{ppc.summary.exact_count}</p>
              <p className="text-[10px] text-gray-500">Exact Match</p>
            </div>
            <div className="rounded border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-lg font-bold text-yellow-400">{ppc.summary.phrase_count}</p>
              <p className="text-[10px] text-gray-500">Phrase Match</p>
            </div>
            <div className="rounded border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-lg font-bold text-blue-400">{ppc.summary.broad_count}</p>
              <p className="text-[10px] text-gray-500">Broad Match</p>
            </div>
            <div className="rounded border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-lg font-bold text-white">${ppc.summary.estimated_daily_budget_usd}</p>
              <p className="text-[10px] text-gray-500">Est. Budget/dzien</p>
            </div>
          </div>

          <MatchSection title="Exact Match" icon={Crosshair} items={ppc.exact_match} color="text-green-400" />
          <MatchSection title="Phrase Match" icon={Target} items={ppc.phrase_match} color="text-yellow-400" />
          <MatchSection title="Broad Match" icon={Globe} items={ppc.broad_match} color="text-blue-400" />

          {ppc.negative_suggestions.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Ban className="h-4 w-4 text-red-400" />
                <h4 className="text-sm font-medium text-gray-300">Sugestie negatywnych</h4>
              </div>
              <div className="flex flex-wrap gap-1">
                {ppc.negative_suggestions.map((kw, i) => (
                  <Badge key={i} variant="secondary" className="bg-red-500/10 text-xs text-red-400">{kw}</Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
