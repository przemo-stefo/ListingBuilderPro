// frontend/src/app/optimize/components/ABTestTab.tsx
// Purpose: A/B test tab — generates 2 listing variants (aggressive vs standard) side-by-side
// NOT for: Single optimization (SingleTab) or batch (BatchTab)

'use client'

import { useState, useMemo } from 'react'
import { Sparkles, Loader2, ArrowLeftRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useTier } from '@/lib/hooks/useTier'
import { generateListing } from '@/lib/api/optimizer'
import { ListingCard } from './ListingCard'
import { ScoresCard } from './ResultDisplay'
import type { OptimizerResponse, OptimizerKeyword } from '@/lib/types'

const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

export default function ABTestTab() {
  const [productTitle, setProductTitle] = useState('')
  const [brand, setBrand] = useState('')
  const [keywordsText, setKeywordsText] = useState('')
  const [marketplace, setMarketplace] = useState('amazon_de')

  const [variantA, setVariantA] = useState<OptimizerResponse | null>(null)
  const [variantB, setVariantB] = useState<OptimizerResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copiedA, setCopiedA] = useState<string | null>(null)
  const [copiedB, setCopiedB] = useState<string | null>(null)

  const { canOptimize, isPremium } = useTier()

  const parsedKeywords = useMemo((): OptimizerKeyword[] => {
    return keywordsText
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => {
        const parts = line.split(/[,;\t]/)
        return {
          phrase: parts[0]?.trim() || '',
          search_volume: parseInt(parts[1]?.trim() || '0', 10) || 0,
        }
      })
      .filter((k) => k.phrase.length > 0)
  }, [keywordsText])

  const canSubmit = productTitle.trim().length >= 3 && brand.trim().length >= 1 && parsedKeywords.length >= 1

  const handleGenerate = async () => {
    if (!canSubmit || !canOptimize) return
    setLoading(true)
    setError('')
    setVariantA(null)
    setVariantB(null)

    const basePayload = {
      product_title: productTitle.trim(),
      brand: brand.trim(),
      keywords: parsedKeywords,
      marketplace,
      product_line: '',
      account_type: 'seller' as const,
    }

    try {
      // WHY: Run both variants in parallel — 2x faster than sequential
      const [resA, resB] = await Promise.all([
        generateListing({ ...basePayload, mode: 'aggressive' }),
        generateListing({ ...basePayload, mode: 'standard' }),
      ])
      setVariantA(resA)
      setVariantB(resB)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Blad generowania wariantow'
      // WHY: 402 = daily free limit or premium-only marketplace — show clear message
      const is402 = msg.includes('402') || msg.toLowerCase().includes('limit') || msg.toLowerCase().includes('premium')
      setError(is402 ? 'Darmowy limit wyczerpany lub marketplace Premium. Wykup subskrypcje aby kontynuowac.' : msg)
    } finally {
      setLoading(false)
    }
  }

  const handleCopyA = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedA(field)
    setTimeout(() => setCopiedA(null), 2000)
  }

  const handleCopyB = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedB(field)
    setTimeout(() => setCopiedB(null), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <ArrowLeftRight className="h-5 w-5" />
            Test A/B — Porownaj warianty
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">Nazwa produktu</label>
              <Input
                value={productTitle}
                onChange={(e) => setProductTitle(e.target.value)}
                placeholder="np. Bluetooth Speaker Waterproof"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Marka</label>
              <Input
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="np. SoundMax"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Slowa kluczowe (1 na linie, opcjonalnie: fraza,wolumen)
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none"
              rows={5}
              value={keywordsText}
              onChange={(e) => setKeywordsText(e.target.value)}
              placeholder={'bluetooth speaker\nwaterproof speaker,12000\nportable speaker outdoor'}
            />
            <span className="text-xs text-gray-500">{parsedKeywords.length} slow kluczowych</span>
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">Marketplace</label>
            <div className="flex flex-wrap gap-2">
              {MARKETPLACES.map((mp) => (
                <Button
                  key={mp.id}
                  variant={marketplace === mp.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMarketplace(mp.id)}
                >
                  {mp.flag} {mp.name}
                </Button>
              ))}
            </div>
          </div>

          {error && (
            <div className="rounded bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={!canSubmit || loading || (!isPremium && !canOptimize)}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generowanie 2 wariantow...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generuj A/B Test
              </>
            )}
          </Button>

          {!isPremium && (
            <p className="text-center text-xs text-gray-500">
              A/B test zuzywa 2 optymalizacje z dziennego limitu
            </p>
          )}
        </CardContent>
      </Card>

      {/* Results side-by-side */}
      {(variantA || variantB) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Variant A */}
          <div className="space-y-4">
            <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/5 px-3 py-2 text-center">
              <span className="text-sm font-medium text-cyan-400">
                Wariant A — Aggressive
              </span>
              {variantA && (
                <span className="ml-2 text-xs text-gray-400">
                  Coverage: {variantA.scores.coverage_pct}%
                </span>
              )}
            </div>
            {variantA && (
              <>
                <ScoresCard scores={variantA.scores} intel={variantA.keyword_intel} />
                <ListingCard
                  listing={variantA.listing}
                  compliance={variantA.compliance}
                  copiedField={copiedA}
                  onCopy={handleCopyA}
                  fullResponse={variantA}
                />
              </>
            )}
          </div>

          {/* Variant B */}
          <div className="space-y-4">
            <div className="rounded-lg border border-purple-500/30 bg-purple-500/5 px-3 py-2 text-center">
              <span className="text-sm font-medium text-purple-400">
                Wariant B — Standard
              </span>
              {variantB && (
                <span className="ml-2 text-xs text-gray-400">
                  Coverage: {variantB.scores.coverage_pct}%
                </span>
              )}
            </div>
            {variantB && (
              <>
                <ScoresCard scores={variantB.scores} intel={variantB.keyword_intel} />
                <ListingCard
                  listing={variantB.listing}
                  compliance={variantB.compliance}
                  copiedField={copiedB}
                  onCopy={handleCopyB}
                  fullResponse={variantB}
                />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
