// frontend/src/app/ad-copy/page.tsx
// Purpose: Ad Copy Generator — AI generates 3 ad variations from product info + RAG knowledge
// NOT for: Listing optimization (that's /optimize) or scoring (that's /listing-score)

'use client'

import { useState } from 'react'
import { Megaphone, Loader2, Plus, X, Copy, Check, Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { PremiumGate } from '@/components/tier/PremiumGate'
import { apiClient } from '@/lib/api/client'

// WHY: Match backend platform options exactly
const PLATFORMS = [
  { id: 'facebook', label: 'Facebook', emoji: 'FB' },
  { id: 'instagram', label: 'Instagram', emoji: 'IG' },
  { id: 'tiktok', label: 'TikTok', emoji: 'TT' },
]

// WHY: Colors per variation type — makes it easy to distinguish at a glance
const VARIATION_STYLES: Record<string, { border: string; bg: string; label: string; accent: string }> = {
  hook: { border: 'border-amber-800', bg: 'bg-amber-900/20', label: 'Hook', accent: 'text-amber-400' },
  story: { border: 'border-blue-800', bg: 'bg-blue-900/20', label: 'Story', accent: 'text-blue-400' },
  benefit: { border: 'border-green-800', bg: 'bg-green-900/20', label: 'Benefit', accent: 'text-green-400' },
}

interface AdVariation {
  type: string
  headline: string
  primary_text: string
  description: string
}

interface AdCopyResult {
  variations: AdVariation[]
  sources_used: number
  sources: string[]
  platform: string
}

export default function AdCopyPage() {
  const [productTitle, setProductTitle] = useState('')
  const [features, setFeatures] = useState<string[]>([''])
  const [targetAudience, setTargetAudience] = useState('')
  const [platform, setPlatform] = useState('facebook')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<AdCopyResult | null>(null)
  const [error, setError] = useState('')
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const validFeatures = features.filter(f => f.trim().length > 0)
  const canSubmit = productTitle.length >= 3 && validFeatures.length >= 1

  const addFeature = () => {
    if (features.length < 10) setFeatures([...features, ''])
  }

  const removeFeature = (idx: number) => {
    if (features.length > 1) setFeatures(features.filter((_, i) => i !== idx))
  }

  const updateFeature = (idx: number, value: string) => {
    setFeatures(features.map((f, i) => i === idx ? value : f))
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const handleGenerate = async () => {
    if (!canSubmit || isLoading) return
    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      // WHY: apiClient sends JWT + License-Key (raw fetch() was missing them)
      const { data } = await apiClient.post<AdCopyResult>('/ads/generate', {
        product_title: productTitle,
        product_features: validFeatures,
        target_audience: targetAudience || undefined,
        platform,
      })
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nieznany błąd')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PremiumGate feature="Reklamy AI">
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-amber-500/20 p-2">
          <Megaphone className="h-6 w-6 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Generator Reklam AI</h1>
          <p className="text-xs text-gray-400">3 warianty reklam na podstawie wiedzy ekspertów e-commerce</p>
        </div>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dane produktu</CardTitle>
          <CardDescription>Podaj informacje o produkcie, który chcesz reklamować</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Nazwa produktu <span className="text-red-400">*</span>
            </label>
            <Input
              value={productTitle}
              onChange={(e) => setProductTitle(e.target.value)}
              placeholder="np. Silikonowy zestaw przyborów kuchennych 12 elementów"
            />
          </div>

          {/* WHY: Dynamic feature list — user adds/removes features, backend needs at least 1 */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Cechy produktu <span className="text-red-400">*</span>
            </label>
            <div className="space-y-2">
              {features.map((feat, idx) => (
                <div key={idx} className="flex gap-2">
                  <Input
                    value={feat}
                    onChange={(e) => updateFeature(idx, e.target.value)}
                    placeholder={`Cecha ${idx + 1}, np. Odporny na temp. do 250°C`}
                  />
                  {features.length > 1 && (
                    <button
                      onClick={() => removeFeature(idx)}
                      className="rounded-lg border border-gray-800 px-2 text-gray-500 hover:border-red-800 hover:text-red-400 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {features.length < 10 && (
              <button
                onClick={addFeature}
                className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
              >
                <Plus className="h-3 w-3" /> Dodaj cechę
              </button>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">Grupa docelowa (opcjonalnie)</label>
            <Input
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="np. Młode mamy szukające trwałych akcesoriów kuchennych"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-400">Platforma</label>
            <div className="flex gap-2">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setPlatform(p.id)}
                  className={cn(
                    'rounded-lg border px-4 py-2 text-sm transition-colors',
                    platform === p.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600'
                  )}
                >
                  <span className="mr-1.5 text-xs text-gray-500">{p.emoji}</span>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generate Button */}
      <Button onClick={handleGenerate} disabled={!canSubmit || isLoading} size="lg">
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="mr-2 h-4 w-4" />
        )}
        {isLoading ? 'Generowanie reklam...' : 'Wygeneruj reklamy'}
      </Button>

      {/* Error */}
      {error && (
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && result.variations.length > 0 && (
        <div className="space-y-4">
          {/* Sources info */}
          {result.sources_used > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <span>Wykorzystano {result.sources_used} źródeł wiedzy:</span>
              {result.sources.map((s, i) => (
                <span key={i} className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400">
                  {s}
                </span>
              ))}
            </div>
          )}

          {/* Ad variation cards */}
          {result.variations.map((v, idx) => {
            const style = VARIATION_STYLES[v.type] || VARIATION_STYLES.hook
            return (
              <Card key={idx} className={cn('border', style.border)}>
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <span className={cn('rounded px-2 py-0.5 text-xs font-bold', style.bg, style.accent)}>
                      {style.label}
                    </span>
                    <CardTitle className="text-base text-white">Wariant {idx + 1}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Headline */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Nagłówek</span>
                      <button
                        onClick={() => copyToClipboard(v.headline, `headline-${idx}`)}
                        className="text-gray-600 hover:text-white transition-colors"
                      >
                        {copiedField === `headline-${idx}` ? (
                          <Check className="h-3 w-3 text-green-400" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                    <p className="text-sm font-semibold text-white">{v.headline}</p>
                  </div>

                  {/* Primary text */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Tekst główny</span>
                      <button
                        onClick={() => copyToClipboard(v.primary_text, `primary-${idx}`)}
                        className="text-gray-600 hover:text-white transition-colors"
                      >
                        {copiedField === `primary-${idx}` ? (
                          <Check className="h-3 w-3 text-green-400" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                    <p className="text-sm text-gray-300 whitespace-pre-wrap">{v.primary_text}</p>
                  </div>

                  {/* Description */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Opis</span>
                      <button
                        onClick={() => copyToClipboard(v.description, `desc-${idx}`)}
                        className="text-gray-600 hover:text-white transition-colors"
                      >
                        {copiedField === `desc-${idx}` ? (
                          <Check className="h-3 w-3 text-green-400" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                    <p className="text-sm text-gray-400">{v.description}</p>
                  </div>

                  {/* Copy All */}
                  <button
                    onClick={() => copyToClipboard(
                      `${v.headline}\n\n${v.primary_text}\n\n${v.description}`,
                      `all-${idx}`
                    )}
                    className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-white transition-colors pt-1"
                  >
                    {copiedField === `all-${idx}` ? (
                      <><Check className="h-3 w-3 text-green-400" /> Skopiowano!</>
                    ) : (
                      <><Copy className="h-3 w-3" /> Kopiuj całość</>
                    )}
                  </button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {result && result.variations.length === 0 && (
        <Card>
          <CardContent className="p-6 text-center text-sm text-gray-400">
            Nie udało się wygenerować reklam. Spróbuj ponownie.
          </CardContent>
        </Card>
      )}
      </div>
    </PremiumGate>
  )
}
