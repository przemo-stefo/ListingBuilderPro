// frontend/src/app/optimize/components/AudienceResearchCard.tsx
// Purpose: Collapsible audience research card — calls OV Skills before optimization
// NOT for: Optimizer logic or result display

'use client'

import { useState } from 'react'
import { Users, ChevronDown, ChevronRight, Loader2, Crown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTier } from '@/lib/hooks/useTier'
import { researchAudience } from '@/lib/api/research'

interface AudienceResearchCardProps {
  productTitle: string
  onResearchComplete: (result: string) => void
}

export default function AudienceResearchCard({
  productTitle,
  onResearchComplete,
}: AudienceResearchCardProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [audience, setAudience] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState('')
  const [error, setError] = useState('')
  const [usedToday, setUsedToday] = useState(false)

  const { isPremium } = useTier()

  // WHY: Free tier = 1 research/day, tracked client-side (backend also enforces rate limit)
  const isLimited = !isPremium && usedToday

  const handleResearch = async () => {
    if (!productTitle || isLimited) return

    setIsLoading(true)
    setError('')

    try {
      const data = await researchAudience({
        product: productTitle,
        audience: audience || `buyers interested in ${productTitle}`,
        skill: 'deep-customer-research',
      })

      setResult(data.result)
      onResearchComplete(data.result)

      if (!isPremium) {
        setUsedToday(true)
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Research failed'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-6"
      >
        <div className="flex items-center gap-3">
          <Users className="h-5 w-5 text-gray-400" />
          <div className="text-left">
            <h3 className="text-lg font-semibold text-white">Badanie odbiorcy</h3>
            <p className="text-sm text-gray-400">Opcjonalne — AI zbada grupe docelowa przed optymalizacja</p>
          </div>
        </div>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <CardContent className="space-y-4 pt-0">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Grupa docelowa
            </label>
            <textarea
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder={productTitle ? `buyers interested in ${productTitle}` : 'np. home cooks 25-45, health-conscious parents'}
              rows={2}
              className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
            />
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleResearch}
              disabled={!productTitle || isLoading || isLimited}
              variant="outline"
              size="sm"
            >
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Users className="mr-2 h-4 w-4" />
              )}
              {isLoading ? 'Badanie trwa...' : 'Zbadaj odbiorce'}
              {isLimited && <Crown className="ml-2 h-3 w-3 text-amber-400" />}
            </Button>
            {isLimited && (
              <span className="text-xs text-amber-400">
                Limit 1/dzien (darmowy plan)
              </span>
            )}
            {!productTitle && (
              <span className="text-xs text-gray-500">
                Najpierw wpisz tytul produktu
              </span>
            )}
          </div>

          {error && (
            <div className="rounded-lg border border-red-900/50 bg-red-900/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {result && (
            <div className="rounded-lg border border-gray-800 bg-[#121212] p-4">
              <h4 className="mb-2 text-sm font-medium text-gray-300">Wynik badania:</h4>
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-400">
                {result}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
