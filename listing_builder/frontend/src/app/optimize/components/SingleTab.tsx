// frontend/src/app/optimize/components/SingleTab.tsx
// Purpose: Single-product listing optimizer — orchestrates form, settings, and results
// NOT for: Batch optimization (BatchTab.tsx), UI components (extracted to own files)

'use client'

import { useState, useRef, useMemo } from 'react'
import { Sparkles, Loader2, ChevronDown, ChevronRight, FileText, Save, FolderOpen, Trash2, X } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useGenerateListing } from '@/lib/hooks/useOptimizer'
import { useTier } from '@/lib/hooks/useTier'
import { useOAuthConnections } from '@/lib/hooks/useOAuth'
import { useToast } from '@/lib/hooks/useToast'
import { FREE_DAILY_LIMIT } from '@/lib/types/tier'
import { useSettings } from '@/lib/hooks/useSettings'
import { useUpdateProduct } from '@/lib/hooks/useProducts'
import { ProductPicker } from './ProductPicker'
import { apiClient } from '@/lib/api/client'
import KeywordsInput, { parseKeywordLines } from './KeywordsInput'
import AudienceResearchCard from './AudienceResearchCard'
import { OriginalDataCard } from './OriginalDataCard'
import { TargetModeCard, LLM_PROVIDERS } from './TargetModeCard'
import { OptimizerResults } from './OptimizerResults'
import { CompetitorImport } from './CompetitorImport'
import { getTemplates, saveTemplate, deleteTemplate } from '@/lib/utils/optimizerTemplates'
import type { OptimizerTemplate } from '@/lib/utils/optimizerTemplates'
import type { OptimizerRequest, OptimizerResponse, LLMProvider, ScoreResult, Product } from '@/lib/types'

// WHY: Marketplace code from scraper (e.g. "DE") → frontend select value (e.g. "amazon_de")
const MARKETPLACE_CODE_MAP: Record<string, string> = {
  US: 'amazon_us', DE: 'amazon_de', UK: 'amazon_uk', FR: 'amazon_fr',
  IT: 'amazon_it', ES: 'amazon_es', PL: 'amazon_pl', NL: 'amazon_nl',
  SE: 'amazon_se', CA: 'amazon_ca', MX: 'amazon_mx', JP: 'amazon_jp',
  AU: 'amazon_au', IN: 'amazon_in', BR: 'amazon_br',
}

interface SingleTabProps {
  loadedResult?: OptimizerResponse | null
  initialTitle?: string
  productId?: string
}

export default function SingleTab({ loadedResult, initialTitle, productId }: SingleTabProps) {
  // Product picker state
  const [pickedProductTitle, setPickedProductTitle] = useState<string | undefined>()
  const [pickedProductId, setPickedProductId] = useState<number | undefined>()
  const [pickedProductImages, setPickedProductImages] = useState<string[]>([])

  // Form state
  const [productTitle, setProductTitle] = useState(initialTitle ?? '')
  const [brand, setBrand] = useState('')
  const [productLine, setProductLine] = useState('')
  const [keywordsText, setKeywordsText] = useState('')
  const [marketplace, setMarketplace] = useState('amazon_de')
  const [mode, setMode] = useState<'aggressive' | 'standard'>('aggressive')
  const [accountType, setAccountType] = useState<'seller' | 'vendor'>('seller')
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('groq')
  const [inlineLlmKey, setInlineLlmKey] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [asin, setAsin] = useState('')
  const [category, setCategory] = useState('')

  // Original listing from import
  const [originalDescription, setOriginalDescription] = useState('')
  const [originalBullets, setOriginalBullets] = useState<string[]>([])

  // Results + scoring
  const [results, setResults] = useState<OptimizerResponse | null>(null)
  const displayResults = loadedResult ?? results
  const [copiedField, setCopiedField] = useState<string | null>(null)
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null)
  const [scoreLoading, setScoreLoading] = useState(false)
  const [savedToProduct, setSavedToProduct] = useState(false)

  // Audience research
  const [audienceContext, setAudienceContext] = useState('')
  const audienceContextRef = useRef(audienceContext)

  // Templates
  const [templates, setTemplates] = useState<OptimizerTemplate[]>(() => getTemplates())
  const [showTemplates, setShowTemplates] = useState(false)
  const [templateName, setTemplateName] = useState('')

  const handleSaveTemplate = () => {
    const name = templateName.trim() || `${marketplace} ${mode} ${brand || 'szablon'}`
    const t = saveTemplate({ name, marketplace, mode, accountType, brand, productLine, category, keywordsText, llmProvider })
    setTemplates(getTemplates())
    setTemplateName('')
    toast({ title: 'Szablon zapisany', description: t.name })
  }

  const handleLoadTemplate = (t: OptimizerTemplate) => {
    setMarketplace(t.marketplace)
    setMode(t.mode as 'aggressive' | 'standard')
    setAccountType(t.accountType as 'seller' | 'vendor')
    setBrand(t.brand)
    setProductLine(t.productLine)
    setCategory(t.category)
    setKeywordsText(t.keywordsText)
    setLlmProvider(t.llmProvider as LLMProvider)
    setShowTemplates(false)
    toast({ title: 'Szablon zaladowany', description: t.name })
  }

  const handleDeleteTemplate = (id: string) => {
    deleteTemplate(id)
    setTemplates(getTemplates())
  }

  // Hooks
  const { data: settingsData } = useSettings()
  const savedLlmKey = settingsData?.llm?.providers?.[llmProvider]?.api_key || ''
  const hasSavedKey = savedLlmKey === '****'
  const { canOptimize, incrementUsage, isPremium, usageToday } = useTier()
  const { data: oauthData } = useOAuthConnections()
  const isAllegroConnected = oauthData?.connections?.some(
    (c) => c.marketplace === 'allegro' && c.status === 'active'
  ) ?? false
  const { toast } = useToast()
  const generateMutation = useGenerateListing()
  const saveToProductMutation = useUpdateProduct()

  const stripHtml = (html: string): string =>
    html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()

  const triggerScore = async (listing: OptimizerResponse['listing']) => {
    setScoreLoading(true)
    setScoreResult(null)
    try {
      const { data } = await apiClient.post<ScoreResult>('/score/listing', {
        title: listing.title, bullets: listing.bullet_points, description: stripHtml(listing.description),
      })
      setScoreResult(data)
    } catch (err) {
      // score is non-critical — fail silently
    } finally {
      setScoreLoading(false)
    }
  }

  const handleImprove = () => {
    if (!scoreResult) return
    const tips = scoreResult.dimensions.filter((d) => d.score < 7).map((d) => `${d.name}: ${d.tip}`).join('\n')
    const newContext = (audienceContext ? audienceContext + '\n\n' : '') + '--- IMPROVEMENT HINTS ---\n' + tips
    setAudienceContext(newContext)
    audienceContextRef.current = newContext
    setTimeout(() => handleGenerate(), 50)
  }

  const effectiveProductId = productId ?? (pickedProductId ? String(pickedProductId) : undefined)

  const handleSaveToProduct = () => {
    if (!effectiveProductId || !displayResults?.listing) return
    const { title, bullet_points, description, backend_keywords } = displayResults.listing
    saveToProductMutation.mutate(
      {
        id: effectiveProductId,
        data: {
          title_optimized: title, description_optimized: description,
          attributes: { bullet_points, seo_keywords: backend_keywords ? backend_keywords.split(',').map((k: string) => k.trim()) : [] },
          status: 'optimized' as const,
        },
      },
      { onSuccess: () => setSavedToProduct(true) },
    )
  }

  const parsedKeywords = useMemo(() => parseKeywordLines(keywordsText), [keywordsText])
  const canSubmit = productTitle.length >= 3 && brand.length >= 1 && parsedKeywords.length >= 1

  const handleProductSelect = (product: Product) => {
    setProductTitle(product.title_original)
    setBrand(product.brand ?? '')
    setAsin(product.source_id ?? '')
    setCategory(product.category ?? '')
    setPickedProductTitle(product.title_original)
    setPickedProductId(product.id)
    setOriginalDescription(stripHtml(product.description_original ?? ''))
    const bp = product.attributes?.bullet_points
    setOriginalBullets(Array.isArray(bp) ? bp as string[] : [])
    setPickedProductImages(Array.isArray(product.images) ? product.images : [])
  }

  const handleProductClear = () => {
    setProductTitle(''); setBrand(''); setAsin(''); setCategory('')
    setPickedProductTitle(undefined); setPickedProductId(undefined)
    setOriginalDescription(''); setOriginalBullets([]); setPickedProductImages([])
  }

  const handleCompetitorImport = (data: {
    title: string; asin: string; marketplace: string; bullets: string[]; description: string
  }) => {
    setProductTitle(data.title)
    setAsin(data.asin)
    if (data.marketplace && MARKETPLACE_CODE_MAP[data.marketplace]) {
      setMarketplace(MARKETPLACE_CODE_MAP[data.marketplace])
    }
    setOriginalBullets(data.bullets)
    setOriginalDescription(data.description)
    toast({ title: 'Listing pobrany', description: `${data.asin} (${data.marketplace}) — uzupelnij marke i slowa kluczowe` })
  }

  const handleGenerate = () => {
    if (!canOptimize()) {
      toast({ title: 'Wymagana subskrypcja', description: 'Optymalizator wymaga aktywnej subskrypcji. Wykup Premium za 19 zł/mies!', variant: 'destructive' })
      return
    }
    const payload: OptimizerRequest = {
      product_title: productTitle, brand, product_line: productLine || undefined,
      keywords: parsedKeywords, marketplace, mode, asin: asin || undefined, category: category || undefined,
      audience_context: audienceContextRef.current || audienceContext || undefined, account_type: accountType,
      ...(llmProvider !== 'groq' && {
        llm_provider: llmProvider,
        ...(LLM_PROVIDERS.find((p) => p.id === llmProvider)?.needsKey && { llm_api_key: inlineLlmKey || undefined }),
      }),
      ...(originalDescription && { original_description: originalDescription }),
      ...(originalBullets.length > 0 && { original_bullets: originalBullets }),
    }
    generateMutation.mutate(payload, {
      onSuccess: (data) => {
        setResults(data); incrementUsage(); setSavedToProduct(false)
        if (data.listing) triggerScore(data.listing)
        if (data.llm_fallback_from) {
          const label = LLM_PROVIDERS.find((p) => p.id === data.llm_fallback_from)?.label || data.llm_fallback_from
          toast({ title: `${label} nie zadziałał`, description: 'Użyto modelu Standardowego jako fallback. Sprawdź klucz w Ustawieniach.', variant: 'destructive' })
        }
      },
    })
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text).catch(() => {})
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const isLoading = generateMutation.isPending

  return (
    <div className="space-y-6">
      <ProductPicker onSelect={handleProductSelect} onClear={handleProductClear} selectedTitle={pickedProductTitle} />

      {isPremium && <CompetitorImport onImport={handleCompetitorImport} />}

      <OriginalDataCard images={pickedProductImages} bullets={originalBullets} description={originalDescription} />

      {/* Product Info */}
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
            <label className="mb-1 block text-sm text-gray-400">Tytul produktu <span className="text-red-400">*</span></label>
            <Input value={productTitle} onChange={(e) => setProductTitle(e.target.value)} placeholder="np. Silikonowy zestaw przyborow kuchennych 12 elementow" />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">Marka <span className="text-red-400">*</span></label>
              <Input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="np. ZULAY" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Linia produktu</label>
              <Input value={productLine} onChange={(e) => setProductLine(e.target.value)} placeholder="np. Premium Kitchen (opcjonalnie)" />
            </div>
          </div>
        </CardContent>
      </Card>

      <AudienceResearchCard productTitle={productTitle} onResearchComplete={setAudienceContext} />
      <KeywordsInput value={keywordsText} onChange={setKeywordsText} />

      <TargetModeCard
        marketplace={marketplace} setMarketplace={setMarketplace}
        mode={mode} setMode={setMode}
        accountType={accountType} setAccountType={setAccountType}
        llmProvider={llmProvider} setLlmProvider={setLlmProvider}
        inlineLlmKey={inlineLlmKey} setInlineLlmKey={setInlineLlmKey}
        isPremium={isPremium} hasSavedKey={hasSavedKey}
      />

      {/* Advanced (collapsible) */}
      <Card>
        <button onClick={() => setShowAdvanced(!showAdvanced)} className="flex w-full items-center justify-between p-6">
          <div>
            <h3 className="text-lg font-semibold text-white">Zaawansowane</h3>
            <p className="text-sm text-gray-400">ASIN, kategoria (opcjonalnie)</p>
          </div>
          {showAdvanced ? <ChevronDown className="h-5 w-5 text-gray-400" /> : <ChevronRight className="h-5 w-5 text-gray-400" />}
        </button>
        {showAdvanced && (
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">ASIN</label>
              <Input value={asin} onChange={(e) => setAsin(e.target.value)} placeholder="B0XXXXXXXX" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Kategoria</label>
              <Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Kuchnia i jadalnia" />
            </div>
          </CardContent>
        )}
      </Card>

      {/* Templates */}
      {isPremium && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowTemplates(!showTemplates)}>
                <FolderOpen className="mr-1 h-3 w-3" />
                Szablony ({templates.length})
              </Button>
              <input
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Nazwa szablonu..."
                className="flex-1 rounded border border-gray-700 bg-[#1A1A1A] px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:border-gray-500 focus:outline-none"
                maxLength={60}
              />
              <Button variant="outline" size="sm" onClick={handleSaveTemplate}>
                <Save className="mr-1 h-3 w-3" />
                Zapisz
              </Button>
            </div>
            {showTemplates && templates.length > 0 && (
              <div className="mt-3 space-y-1 max-h-48 overflow-y-auto">
                {templates.map((t) => (
                  <div key={t.id} className="flex items-center justify-between rounded border border-gray-800 px-3 py-2 text-xs">
                    <button onClick={() => handleLoadTemplate(t)} className="flex-1 text-left text-white hover:text-gray-300">
                      <span className="font-medium">{t.name}</span>
                      <span className="ml-2 text-gray-500">{t.marketplace} · {t.mode}</span>
                    </button>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => handleDeleteTemplate(t.id)}>
                      <Trash2 className="h-3 w-3 text-gray-500 hover:text-red-400" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            {showTemplates && templates.length === 0 && (
              <p className="mt-3 text-xs text-gray-500">Brak zapisanych szablonow. Wypelnij formularz i kliknij Zapisz.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Generate Button */}
      <div className="flex items-center gap-3">
        <Button onClick={handleGenerate} disabled={!canSubmit || isLoading || !canOptimize()} size="lg">
          {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
          {isLoading ? 'Generowanie listingu...' : 'Wygeneruj zoptymalizowany listing'}
        </Button>
        {!isPremium && (
          <span className="text-xs text-amber-400">
            Wymagana subskrypcja
          </span>
        )}
        {isLoading && <span className="text-xs text-gray-500 animate-pulse">AI generuje listing...</span>}
        {generateMutation.isError && !isLoading && (
          <span className="text-xs text-red-400">
            {(generateMutation.error as Error & { code?: string })?.code === '402' ? 'Dzienny limit — wykup Premium'
              : (generateMutation.error as Error & { code?: string })?.code === '503' ? 'Serwer AI przeciążony — spróbuj za minutę'
              : 'Błąd — kliknij ponownie'}
          </span>
        )}
      </div>

      {/* Results */}
      {displayResults && (
        <OptimizerResults
          displayResults={displayResults}
          scoreResult={scoreResult} scoreLoading={scoreLoading} onImprove={handleImprove}
          copiedField={copiedField} onCopy={copyToClipboard} isAllegroConnected={isAllegroConnected}
          productName={productTitle} brand={brand} category={category} marketplace={marketplace}
          effectiveProductId={effectiveProductId} savedToProduct={savedToProduct}
          onSaveToProduct={handleSaveToProduct} savePending={saveToProductMutation.isPending}
          onRetry={handleGenerate} canRetry={canSubmit} isLoading={isLoading}
        />
      )}
    </div>
  )
}
