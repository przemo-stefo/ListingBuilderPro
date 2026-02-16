// frontend/src/app/optimize/components/KeywordIntelCard.tsx
// Purpose: Keyword tier distribution and missing keywords display (premium-gated)
// NOT for: Other result display components

'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FeatureGate } from '@/components/tier/FeatureGate'
import type { OptimizerResponse } from '@/lib/types'

// WHY: Shows keyword tier distribution and missing keywords
export function KeywordIntelCard({ intel }: { intel: OptimizerResponse['keyword_intel'] }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <FeatureGate mode="blur">
      <Card>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between p-6"
        >
          <div>
            <h3 className="text-lg font-semibold text-white">Analiza slow kluczowych</h3>
            <p className="text-sm text-gray-400">
              {intel.total_analyzed} slow przeanalizowanych w 3 warstwach
            </p>
          </div>
          {expanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {expanded && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
                <p className="text-xs text-gray-500">Warstwa 1 (Tytul)</p>
                <p className="text-xl font-bold text-white">{intel.tier1_title}</p>
              </div>
              <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
                <p className="text-xs text-gray-500">Warstwa 2 (Punkty)</p>
                <p className="text-xl font-bold text-white">{intel.tier2_bullets}</p>
              </div>
              <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
                <p className="text-xs text-gray-500">Warstwa 3 (Backend)</p>
                <p className="text-xl font-bold text-white">{intel.tier3_backend}</p>
              </div>
            </div>
            {intel.missing_keywords.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-300">
                  Brakujace slowa kluczowe ({intel.missing_keywords.length})
                </h4>
                <div className="flex flex-wrap gap-1">
                  {intel.missing_keywords.map((kw, i) => (
                    <Badge key={i} variant="secondary" className="bg-red-500/10 text-red-400 text-[10px]">
                      {kw}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {intel.root_words.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-300">Najczestsze rdzenie slow</h4>
                <div className="flex flex-wrap gap-1">
                  {intel.root_words.map((rw, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px]">
                      {rw.word} ({rw.frequency})
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </FeatureGate>
  )
}
