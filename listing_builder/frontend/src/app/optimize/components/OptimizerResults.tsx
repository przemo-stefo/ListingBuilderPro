// frontend/src/app/optimize/components/OptimizerResults.tsx
// Purpose: Display optimization results — scores, listing, keywords, PPC, images, save button
// NOT for: Form logic or generation (that's SingleTab.tsx)

'use client'

import { Loader2, Database, XCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScoresCard } from './ResultDisplay'
import { ListingCard } from './ListingCard'
import { RankingJuiceCard } from './RankingJuiceCard'
import { FeedbackWidget } from './FeedbackWidget'
import { KeywordIntelCard } from './KeywordIntelCard'
import { PPCRecommendationsCard } from './PPCRecommendationsCard'
import { ListingScoreCard } from './ListingScoreCard'
import ImageGenerator from './ImageGenerator'
import type { OptimizerResponse, ScoreResult } from '@/lib/types'

interface OptimizerResultsProps {
  displayResults: OptimizerResponse
  scoreResult: ScoreResult | null
  scoreLoading: boolean
  onImprove: () => void
  copiedField: string | null
  onCopy: (text: string, field: string) => void
  isAllegroConnected: boolean
  // Image generator props
  productName: string
  brand: string
  category: string
  marketplace: string
  // Save to product
  effectiveProductId?: string
  savedToProduct: boolean
  onSaveToProduct: () => void
  savePending: boolean
  // Retry on error
  onRetry: () => void
  canRetry: boolean
  isLoading: boolean
}

export function OptimizerResults({
  displayResults, scoreResult, scoreLoading, onImprove,
  copiedField, onCopy, isAllegroConnected,
  productName, brand, category, marketplace,
  effectiveProductId, savedToProduct, onSaveToProduct, savePending,
  onRetry, canRetry, isLoading,
}: OptimizerResultsProps) {
  if (displayResults.status === 'error') {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <XCircle className="h-5 w-5" />
              <span>Optymalizacja nie powiodla sie. Sprawdz logi workflow.</span>
            </div>
            <Button onClick={onRetry} disabled={!canRetry || isLoading} size="sm" variant="outline">
              Spróbuj ponownie
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (displayResults.status !== 'success' && displayResults.status !== 'completed') return null

  return (
    <div className="space-y-4">
      {displayResults.ranking_juice && (
        <RankingJuiceCard
          rankingJuice={displayResults.ranking_juice}
          optimizationSource={displayResults.optimization_source}
        />
      )}
      {scoreLoading && (
        <Card>
          <CardContent className="flex items-center gap-3 p-6">
            <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
            <span className="text-sm text-gray-400">Oceniamy Twoj listing...</span>
          </CardContent>
        </Card>
      )}
      {scoreResult && (
        <ListingScoreCard scoreResult={scoreResult} onImprove={onImprove} />
      )}
      <ScoresCard scores={displayResults.scores} intel={displayResults.keyword_intel} coverageBreakdown={displayResults.coverage_breakdown} llmProvider={displayResults.llm_provider} />
      <ListingCard
        listing={displayResults.listing}
        compliance={displayResults.compliance}
        copiedField={copiedField}
        onCopy={onCopy}
        fullResponse={displayResults}
        isAllegroConnected={isAllegroConnected}
      />
      <KeywordIntelCard intel={displayResults.keyword_intel} />
      {displayResults.ppc_recommendations && (
        <PPCRecommendationsCard ppc={displayResults.ppc_recommendations} />
      )}
      <FeedbackWidget listingHistoryId={displayResults.listing_history_id} />
      <ImageGenerator
        productName={productName}
        brand={brand}
        bulletPoints={displayResults.listing.bullet_points}
        description={displayResults.listing.description}
        category={category}
        language={marketplace.startsWith('amazon_de') ? 'de' : marketplace.startsWith('amazon_pl') ? 'pl' : 'en'}
      />
      {effectiveProductId && (
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-300">
                {savedToProduct ? 'Listing zapisany do produktu' : 'Zapisz zoptymalizowany listing do Bazy Produktow'}
              </span>
            </div>
            <Button
              onClick={onSaveToProduct}
              disabled={savedToProduct || savePending}
              variant={savedToProduct ? 'ghost' : 'outline'}
              size="sm"
            >
              {savePending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
              ) : savedToProduct ? (
                '✓ Zapisano'
              ) : (
                <><Database className="h-3.5 w-3.5 mr-1.5" /> Zapisz do produktu</>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
