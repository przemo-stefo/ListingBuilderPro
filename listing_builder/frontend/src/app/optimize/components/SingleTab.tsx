// frontend/src/app/optimize/components/SingleTab.tsx
// Purpose: Single-product listing optimizer form — extracted from page.tsx
// NOT for: Batch optimization (that's BatchTab.tsx)

'use client'

import { useState } from 'react'
import {
  Sparkles,
  Loader2,
  ChevronDown,
  ChevronRight,
  XCircle,
  FileText,
  Hash,
  Zap,
  Target,
  Database,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useGenerateListing } from '@/lib/hooks/useOptimizer'
import { useTier } from '@/lib/hooks/useTier'
import { useOAuthConnections } from '@/lib/hooks/useOAuth'
import { useToast } from '@/lib/hooks/useToast'
import { FREE_DAILY_LIMIT } from '@/lib/types/tier'
import { ScoresCard } from './ResultDisplay'
import { ListingCard } from './ListingCard'
import { RankingJuiceCard } from './RankingJuiceCard'
import { FeedbackWidget } from './FeedbackWidget'
import { KeywordIntelCard } from './KeywordIntelCard'
import AudienceResearchCard from './AudienceResearchCard'
import { PPCRecommendationsCard } from './PPCRecommendationsCard'
import { useSettings } from '@/lib/hooks/useSettings'
import { useUpdateProduct } from '@/lib/hooks/useProducts'
import { ListingScoreCard } from './ListingScoreCard'
import { ProductPicker } from './ProductPicker'
import type { OptimizerRequest, OptimizerResponse, OptimizerKeyword, LLMProvider, ScoreResult, Product } from '@/lib/types'

// WHY: Same provider list as settings — keeps UI consistent
const LLM_PROVIDERS: { id: LLMProvider; label: string; hint: string }[] = [
  { id: 'groq', label: 'Groq (w cenie)', hint: 'Llama 3.3 70B — darmowy' },
  { id: 'gemini_flash', label: 'Gemini Flash', hint: 'Szybki i tani' },
  { id: 'gemini_pro', label: 'Gemini Pro', hint: 'Najlepsza jakosc' },
  { id: 'openai', label: 'OpenAI', hint: 'GPT-4o Mini' },
]

// WHY: Marketplace options match what the n8n workflow supports
const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

interface SingleTabProps {
  loadedResult?: OptimizerResponse | null
  // WHY: Allegro Manager passes ?prefill=title to pre-populate the form
  initialTitle?: string
  // WHY: When coming from product detail page, we can save optimized listing back to the product
  productId?: string
}

export default function SingleTab({ loadedResult, initialTitle, productId }: SingleTabProps) {
  // WHY: Track whether form was filled from product picker (vs manual input)
  const [pickedProductTitle, setPickedProductTitle] = useState<string | undefined>()

  // Form state — WHY initialTitle: prefill from Allegro Manager's "Optymalizuj z AI" button
  const [productTitle, setProductTitle] = useState(initialTitle ?? '')
  const [brand, setBrand] = useState('')
  const [productLine, setProductLine] = useState('')
  const [keywordsText, setKeywordsText] = useState('')
  const [marketplace, setMarketplace] = useState('amazon_de')
  const [mode, setMode] = useState<'aggressive' | 'standard'>('aggressive')
  const [accountType, setAccountType] = useState<'seller' | 'vendor'>('seller')
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('groq')
  const [inlineLlmKey, setInlineLlmKey] = useState('')

  // WHY: Read saved LLM settings — masked keys mean user saved a key in Settings
  const { data: settingsData } = useSettings()
  const savedLlmKey = settingsData?.llm?.providers?.[llmProvider]?.api_key || ''
  // WHY: Masked key (****) means backend HAS a saved key — backend will read it directly
  const hasSavedKey = savedLlmKey.length > 0 && savedLlmKey !== '****'

  // Results — use loaded result from history if provided
  const [results, setResults] = useState<OptimizerResponse | null>(null)
  const displayResults = loadedResult ?? results
  const [copiedField, setCopiedField] = useState<string | null>(null)

  // WHY: Auto-score state — fires after optimization completes
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null)
  const [scoreLoading, setScoreLoading] = useState(false)

  // WHY: Audience research result feeds into optimizer as LLM context
  const [audienceContext, setAudienceContext] = useState('')

  // Collapsible sections
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [asin, setAsin] = useState('')
  const [category, setCategory] = useState('')

  // Tier
  const { canOptimize, incrementUsage, isPremium, usageToday } = useTier()

  // WHY: Show "Aktualizuj na Allegro" button only when OAuth connected
  const { data: oauthData } = useOAuthConnections()
  const isAllegroConnected = oauthData?.connections?.some(
    (c) => c.marketplace === 'allegro' && c.status === 'active'
  ) ?? false
  const { toast } = useToast()

  // Hooks
  const generateMutation = useGenerateListing()
  const saveToProductMutation = useUpdateProduct()
  const [savedToProduct, setSavedToProduct] = useState(false)

  // WHY: Score API expects plain text, but optimizer returns HTML description
  const stripHtml = (html: string): string =>
    html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()

  // WHY: Auto-trigger listing score after optimization to close the feedback loop
  const triggerScore = async (listing: OptimizerResponse['listing']) => {
    setScoreLoading(true)
    setScoreResult(null)
    try {
      const res = await fetch('/api/proxy/score/listing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: listing.title,
          bullets: listing.bullet_points,
          description: stripHtml(listing.description),
        }),
      })
      if (res.ok) {
        const data: ScoreResult = await res.json()
        setScoreResult(data)
      }
    } catch {
      // WHY: Score is non-critical — don't break the flow if it fails
    } finally {
      setScoreLoading(false)
    }
  }

  // WHY: "Popraw" button — re-generates with improvement hints from low-scoring dimensions
  const handleImprove = () => {
    if (!scoreResult) return
    const tips = scoreResult.dimensions
      .filter((d) => d.score < 7)
      .map((d) => `${d.name}: ${d.tip}`)
      .join('\n')
    // WHY: Inject tips into audience_context so LLM uses them as improvement guidance
    setAudienceContext((prev) => {
      const prefix = prev ? prev + '\n\n' : ''
      return prefix + '--- IMPROVEMENT HINTS ---\n' + tips
    })
    // WHY: Small delay to ensure state updates before re-trigger
    setTimeout(() => handleGenerate(), 50)
  }

  // WHY: Bridge between Optimizer and Product Database — saves optimized listing back to the product
  const handleSaveToProduct = () => {
    if (!productId || !displayResults?.listing) return
    const { title, bullet_points, description, backend_keywords } = displayResults.listing
    saveToProductMutation.mutate(
      {
        id: productId,
        data: {
          title_optimized: title,
          description_optimized: description,
          attributes: {
            bullet_points,
            seo_keywords: backend_keywords ? backend_keywords.split(',').map((k: string) => k.trim()) : [],
          },
          status: 'optimized' as const,
        },
      },
      { onSuccess: () => setSavedToProduct(true) },
    )
  }

  // WHY: Parse keywords from textarea — supports CSV (phrase,volume) and plain text (one per line)
  const parseKeywords = (): OptimizerKeyword[] => {
    return keywordsText
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => {
        // Try CSV format: "keyword phrase,1234"
        const commaIdx = line.lastIndexOf(',')
        if (commaIdx > 0) {
          const phrase = line.substring(0, commaIdx).trim().replace(/^["']|["']$/g, '')
          const vol = parseInt(line.substring(commaIdx + 1).trim())
          if (!isNaN(vol) && vol > 0) {
            return { phrase, search_volume: vol }
          }
        }
        // Plain text — no volume
        return { phrase: line.replace(/^["']|["']$/g, ''), search_volume: 0 }
      })
  }

  const keywordCount = parseKeywords().length
  const canSubmit = productTitle.length >= 3 && brand.length >= 1 && keywordCount >= 1

  // WHY: Auto-fill form fields when user picks a product from the database
  const handleProductSelect = (product: Product) => {
    setProductTitle(product.title_original)
    setBrand(product.brand ?? '')
    setAsin(product.source_id ?? '')
    setCategory(product.category ?? '')
    setPickedProductTitle(product.title_original)
  }

  const handleProductClear = () => {
    setProductTitle('')
    setBrand('')
    setAsin('')
    setCategory('')
    setPickedProductTitle(undefined)
  }

  const handleGenerate = () => {
    // WHY: Free tier daily limit check
    if (!canOptimize()) {
      toast({
        title: 'Dzienny limit osiagniety',
        description: `Darmowy plan pozwala na ${FREE_DAILY_LIMIT} optymalizacje dziennie. Odblokuj Premium!`,
        variant: 'destructive',
      })
      return
    }

    const payload: OptimizerRequest = {
      product_title: productTitle,
      brand,
      product_line: productLine || undefined,
      keywords: parseKeywords(),
      marketplace,
      mode,
      asin: asin || undefined,
      category: category || undefined,
      audience_context: audienceContext || undefined,
      account_type: accountType,
      // WHY: Only send provider info when not default Groq
      ...(llmProvider !== 'groq' && {
        llm_provider: llmProvider,
        llm_api_key: inlineLlmKey || undefined,
      }),
    }

    generateMutation.mutate(payload, {
      onSuccess: (data) => {
        setResults(data)
        incrementUsage()
        setSavedToProduct(false)
        // WHY: Auto-score the generated listing to show quality feedback
        if (data.listing) triggerScore(data.listing)
        // WHY: Warn user when their chosen provider failed and Groq was used instead
        if (data.llm_fallback_from) {
          const providerLabel = LLM_PROVIDERS.find((p) => p.id === data.llm_fallback_from)?.label || data.llm_fallback_from
          toast({
            title: `${providerLabel} nie zadziałał`,
            description: 'Klucz API jest nieprawidłowy lub wygasł. Użyto Groq jako fallback. Sprawdź klucz w Ustawieniach.',
            variant: 'destructive',
          })
        }
      },
    })
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const isLoading = generateMutation.isPending

  return (
    <div className="space-y-6">
      {/* WHY: Product picker — lets user select from imported products instead of typing manually */}
      <ProductPicker
        onSelect={handleProductSelect}
        onClear={handleProductClear}
        selectedTitle={pickedProductTitle}
      />

      {/* Section 1: Product Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Informacje o produkcie</CardTitle>
          </div>
          <CardDescription>Podstawowe dane produktu do listingu</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Tytul produktu <span className="text-red-400">*</span>
            </label>
            <Input
              value={productTitle}
              onChange={(e) => setProductTitle(e.target.value)}
              placeholder="np. Silikonowy zestaw przyborow kuchennych 12 elementow"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Marka <span className="text-red-400">*</span>
              </label>
              <Input
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="np. ZULAY"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Linia produktu</label>
              <Input
                value={productLine}
                onChange={(e) => setProductLine(e.target.value)}
                placeholder="np. Premium Kitchen (opcjonalnie)"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audience Research (optional, between product info and keywords) */}
      <AudienceResearchCard
        productTitle={productTitle}
        onResearchComplete={setAudienceContext}
      />

      {/* Section 2: Keywords */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Hash className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Slowa kluczowe</CardTitle>
          </div>
          <CardDescription>
            Wklej slowa kluczowe, po jednym w linii. Opcjonalnie dodaj wolumen wyszukiwan po przecinku.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <textarea
            value={keywordsText}
            onChange={(e) => setKeywordsText(e.target.value)}
            placeholder={
              'silicone kitchen utensils,12000\nkitchen utensil set,8500\ncooking utensils silicone,6200\nheat resistant spatula,3400\nnon stick cooking tools'
            }
            rows={8}
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
          />
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>
              Wykryto {keywordCount} {keywordCount === 1 ? 'slowo' : keywordCount < 5 ? 'slowa' : 'slow'}
            </span>
            <span>Format: fraza kluczowa,wolumen (wolumen opcjonalny)</span>
          </div>
        </CardContent>
      </Card>

      {/* Section 3: Marketplace & Mode */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Cel i tryb</CardTitle>
          </div>
          <CardDescription>Wybierz marketplace, tryb optymalizacji, typ konta i model AI</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-gray-400">Marketplace</label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              {MARKETPLACES.map((mp) => {
                // WHY: Free tier = Amazon only
                const isAmazon = mp.id.startsWith('amazon')
                const isLocked = !isPremium && !isAmazon
                return (
                  <button
                    key={mp.id}
                    onClick={() => !isLocked && setMarketplace(mp.id)}
                    disabled={isLocked}
                    title={isLocked ? 'Dostepne w Premium' : undefined}
                    className={cn(
                      'rounded-lg border px-3 py-2 text-sm transition-colors relative',
                      isLocked
                        ? 'border-gray-800 text-gray-600 cursor-not-allowed opacity-50'
                        : marketplace === mp.id
                          ? 'border-white bg-white/5 text-white'
                          : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                    )}
                  >
                    <span className="mr-1 text-xs">{mp.flag}</span>
                    {mp.name}
                    {isLocked && <span className="ml-1 text-[10px] text-amber-400">PRO</span>}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-400">Tryb optymalizacji</label>
            <div className="flex gap-2">
              <button
                onClick={() => setMode('aggressive')}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                  mode === 'aggressive'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                <Zap className="h-4 w-4" />
                Agresywny
                <span className="text-[10px] text-gray-500">96%+ pokrycie</span>
              </button>
              <button
                onClick={() => setMode('standard')}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                  mode === 'standard'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                <Target className="h-4 w-4" />
                Standardowy
                <span className="text-[10px] text-gray-500">82%+ pokrycie</span>
              </button>
            </div>
          </div>

          {/* WHY: Vendor accounts get 10 bullet points instead of 5 */}
          <div>
            <label className="mb-2 block text-sm text-gray-400">Typ konta Amazon</label>
            <div className="flex gap-2">
              <button
                onClick={() => setAccountType('seller')}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm transition-colors',
                  accountType === 'seller'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                Seller
                <span className="ml-1 text-[10px] text-gray-500">5 bulletow</span>
              </button>
              <button
                onClick={() => setAccountType('vendor')}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm transition-colors',
                  accountType === 'vendor'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                Vendor
                <span className="ml-1 text-[10px] text-gray-500">10 bulletow</span>
              </button>
            </div>
          </div>

          {/* WHY: LLM provider picker — lets user choose Gemini/OpenAI per optimization */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Model AI</label>
            <p className="mb-2 text-[10px] text-gray-500">Silnik AI generujacy listing. Groq jest darmowy. Inne wymagaja klucza API (zapisz go w Ustawieniach).</p>
            <div className="flex flex-wrap gap-2">
              {LLM_PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => { setLlmProvider(p.id); setInlineLlmKey('') }}
                  title={p.hint}
                  className={cn(
                    'rounded-lg border px-3 py-1.5 text-sm transition-colors',
                    llmProvider === p.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600'
                  )}
                >
                  {p.label}
                  <span className="ml-1 text-[9px] text-gray-600">{p.hint}</span>
                </button>
              ))}
            </div>
            {/* WHY: Show inline key input when no saved key for this provider */}
            {llmProvider !== 'groq' && !hasSavedKey && (
              <div className="mt-2">
                <Input
                  type="password"
                  value={inlineLlmKey}
                  onChange={(e) => setInlineLlmKey(e.target.value)}
                  placeholder="Wklej klucz API (lub zapisz w Ustawieniach)"
                  className="text-sm"
                />
              </div>
            )}
            {llmProvider !== 'groq' && hasSavedKey && (
              <p className="mt-1 text-[10px] text-gray-500">Uzyje klucza zapisanego w Ustawieniach</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Section 4: Advanced (collapsible) */}
      <Card>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex w-full items-center justify-between p-6"
        >
          <div>
            <h3 className="text-lg font-semibold text-white">Zaawansowane</h3>
            <p className="text-sm text-gray-400">ASIN, kategoria (opcjonalnie)</p>
          </div>
          {showAdvanced ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {showAdvanced && (
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">ASIN</label>
              <Input
                value={asin}
                onChange={(e) => setAsin(e.target.value)}
                placeholder="B0XXXXXXXX"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Kategoria</label>
              <Input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Kuchnia i jadalnia"
              />
            </div>
          </CardContent>
        )}
      </Card>

      {/* Generate Button */}
      <div className="flex items-center gap-3">
        <Button onClick={handleGenerate} disabled={!canSubmit || isLoading || !canOptimize()} size="lg">
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          {isLoading ? 'Generowanie listingu...' : 'Wygeneruj zoptymalizowany listing'}
        </Button>
        {!isPremium && (
          <span className={cn(
            'text-xs',
            usageToday >= FREE_DAILY_LIMIT ? 'text-red-400' : 'text-gray-500'
          )}>
            {usageToday}/{FREE_DAILY_LIMIT} optymalizacje dzis
          </span>
        )}
        {isLoading && (
          <span className="text-xs text-gray-500">
            AI pisze tytul, bullety i opis...
          </span>
        )}
      </div>

      {/* Results */}
      {displayResults && (displayResults.status === 'success' || displayResults.status === 'completed') && (
        <div className="space-y-4">
          {displayResults.ranking_juice && (
            <RankingJuiceCard
              rankingJuice={displayResults.ranking_juice}
              optimizationSource={displayResults.optimization_source}
            />
          )}
          {/* WHY: Auto-score card — shows listing quality right after optimization */}
          {scoreLoading && (
            <Card>
              <CardContent className="flex items-center gap-3 p-6">
                <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                <span className="text-sm text-gray-400">Oceniamy Twoj listing...</span>
              </CardContent>
            </Card>
          )}
          {scoreResult && (
            <ListingScoreCard scoreResult={scoreResult} onImprove={handleImprove} />
          )}
          <ScoresCard scores={displayResults.scores} intel={displayResults.keyword_intel} coverageBreakdown={displayResults.coverage_breakdown} llmProvider={displayResults.llm_provider} />
          <ListingCard
            listing={displayResults.listing}
            compliance={displayResults.compliance}
            copiedField={copiedField}
            onCopy={copyToClipboard}
            fullResponse={displayResults}
            isAllegroConnected={isAllegroConnected}
          />
          <KeywordIntelCard intel={displayResults.keyword_intel} />
          {displayResults.ppc_recommendations && (
            <PPCRecommendationsCard ppc={displayResults.ppc_recommendations} />
          )}
          <FeedbackWidget listingHistoryId={displayResults.listing_history_id} />
          {/* WHY: Bridge — saves optimized listing back to the product in DB */}
          {productId && (
            <Card>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-300">
                    {savedToProduct
                      ? 'Listing zapisany do produktu'
                      : 'Zapisz zoptymalizowany listing do Bazy Produktow'}
                  </span>
                </div>
                <Button
                  onClick={handleSaveToProduct}
                  disabled={savedToProduct || saveToProductMutation.isPending}
                  variant={savedToProduct ? 'ghost' : 'outline'}
                  size="sm"
                >
                  {saveToProductMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                  ) : savedToProduct ? (
                    '✓ Zapisano'
                  ) : (
                    <>
                      <Database className="h-3.5 w-3.5 mr-1.5" />
                      Zapisz do produktu
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {displayResults && displayResults.status === 'error' && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-400">
              <XCircle className="h-5 w-5" />
              <span>Optymalizacja nie powiodla sie. Sprawdz logi workflow.</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
