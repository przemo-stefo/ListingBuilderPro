// frontend/src/app/listing-score/page.tsx
// Purpose: Listing Score — AI rates listing quality 1-10 on 5 copywriting dimensions
// NOT for: Listing generation (that's /optimize) or ad copy (that's /ad-copy)

'use client'

import { useState } from 'react'
import { BarChart3, Loader2, Plus, X, Sparkles, TrendingUp, AlertTriangle, CheckCircle2, Link2, Search } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'

interface DimensionScore {
  name: string
  score: number
  explanation: string
  tip: string
}

interface ScoreResult {
  overall_score: number
  dimensions: DimensionScore[]
  sources_used: number
}

interface FetchResult {
  asin: string
  marketplace: string
  title: string
  bullets: string[]
  description: string
  url: string
  error: string
}

// WHY: Map domain suffixes to marketplace labels for smart detection in the UI
const AMAZON_DOMAINS: Record<string, string> = {
  'amazon.com': '🇺🇸 US', 'amazon.co.uk': '🇬🇧 UK', 'amazon.de': '🇩🇪 DE',
  'amazon.fr': '🇫🇷 FR', 'amazon.it': '🇮🇹 IT', 'amazon.es': '🇪🇸 ES',
  'amazon.pl': '🇵🇱 PL', 'amazon.nl': '🇳🇱 NL', 'amazon.se': '🇸🇪 SE',
  'amazon.ca': '🇨🇦 CA', 'amazon.co.jp': '🇯🇵 JP', 'amazon.com.au': '🇦🇺 AU',
  'amazon.in': '🇮🇳 IN', 'amazon.com.br': '🇧🇷 BR', 'amazon.sa': '🇸🇦 SA',
  'amazon.ae': '🇦🇪 AE', 'amazon.sg': '🇸🇬 SG', 'amazon.com.tr': '🇹🇷 TR',
  'amazon.com.be': '🇧🇪 BE', 'amazon.com.mx': '🇲🇽 MX', 'amazon.eg': '🇪🇬 EG',
}

// WHY: Client-side detection gives instant feedback before hitting backend
function detectInput(raw: string): { type: 'url' | 'asin' | 'unknown'; asin: string; marketplace: string } {
  const trimmed = raw.trim()
  if (!trimmed) return { type: 'unknown', asin: '', marketplace: '' }

  // URL detection
  if (trimmed.startsWith('http')) {
    try {
      const url = new URL(trimmed)
      const host = url.hostname.replace('www.', '')
      const mp = AMAZON_DOMAINS[host] || ''

      // Extract ASIN from path
      const dpMatch = url.pathname.match(/\/dp\/([A-Z0-9]{10})/i)
      const gpMatch = url.pathname.match(/\/gp\/product\/([A-Z0-9]{10})/i)
      const asin = (dpMatch?.[1] || gpMatch?.[1] || '').toUpperCase()

      return { type: 'url', asin, marketplace: mp }
    } catch {
      return { type: 'unknown', asin: '', marketplace: '' }
    }
  }

  // Bare ASIN detection (10 alphanumeric chars)
  if (/^[A-Z0-9]{10}$/i.test(trimmed)) {
    return { type: 'asin', asin: trimmed.toUpperCase(), marketplace: '' }
  }

  return { type: 'unknown', asin: '', marketplace: '' }
}

// WHY: Color-code scores so user instantly sees what's good/bad
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
  if (score >= 8) return <CheckCircle2 className="h-4 w-4 text-green-400" />
  if (score >= 6) return <TrendingUp className="h-4 w-4 text-amber-400" />
  return <AlertTriangle className="h-4 w-4 text-red-400" />
}

// WHY: Progress bar gives visual weight to each dimension
function ScoreBar({ score }: { score: number }) {
  const pct = (score / 10) * 100
  const color = score >= 8 ? 'bg-green-500' : score >= 6 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="h-1.5 w-full rounded-full bg-gray-800">
      <div className={cn('h-1.5 rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function ListingScorePage() {
  const [title, setTitle] = useState('')
  const [bullets, setBullets] = useState<string[]>(['', '', '', '', ''])
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ScoreResult | null>(null)
  const [error, setError] = useState('')

  // WHY: Smart import state — separate from form state
  const [importInput, setImportInput] = useState('')
  const [importLoading, setImportLoading] = useState(false)
  const [importError, setImportError] = useState('')
  const [detectedInfo, setDetectedInfo] = useState<{ type: string; asin: string; marketplace: string }>({ type: 'unknown', asin: '', marketplace: '' })

  const validBullets = bullets.filter(b => b.trim().length > 0)
  const canSubmit = title.length >= 3 && validBullets.length >= 1

  // WHY: Live detection on input change for instant feedback
  const handleImportChange = (value: string) => {
    setImportInput(value)
    setImportError('')
    setDetectedInfo(detectInput(value))
  }

  const handleFetch = async () => {
    if (!importInput.trim() || importLoading) return
    setImportLoading(true)
    setImportError('')

    try {
      // WHY: apiClient sends JWT + License-Key (raw fetch() was missing them)
      const { data } = await apiClient.post<FetchResult>('/score/fetch', { input: importInput.trim() })

      if (data.error && !data.title) {
        setImportError(data.error)
        return
      }

      // WHY: Auto-fill form with fetched data
      if (data.title) setTitle(data.title)
      if (data.bullets.length > 0) {
        setBullets(data.bullets.length >= 5 ? data.bullets : [...data.bullets, ...Array(5 - data.bullets.length).fill('')])
      }
      if (data.description) setDescription(data.description)

      // WHY: Show warning if fetch partially failed
      if (data.error) setImportError(data.error)

    } catch (e) {
      setImportError(e instanceof Error ? e.message : 'Błąd pobierania')
    } finally {
      setImportLoading(false)
    }
  }

  const addBullet = () => {
    if (bullets.length < 10) setBullets([...bullets, ''])
  }

  const removeBullet = (idx: number) => {
    if (bullets.length > 1) setBullets(bullets.filter((_, i) => i !== idx))
  }

  const updateBullet = (idx: number, value: string) => {
    setBullets(bullets.map((b, i) => i === idx ? value : b))
  }

  const handleScore = async () => {
    if (!canSubmit || isLoading) return
    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      // WHY: apiClient sends JWT + License-Key (raw fetch() was missing them)
      const { data } = await apiClient.post<ScoreResult>('/score/listing', {
        title,
        bullets: validBullets,
        description: description || undefined,
      })
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nieznany błąd')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-blue-500/20 p-2">
          <BarChart3 className="h-6 w-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Listing Score</h1>
          <p className="text-xs text-gray-400">Oceń jakość listingu w 5 wymiarach copywriterskich</p>
        </div>
      </div>

      {/* Smart Import */}
      <Card className="border-gray-800">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Link2 className="h-4 w-4 text-gray-400" />
            <CardTitle className="text-sm font-medium text-gray-300">Szybki import z Amazon</CardTitle>
          </div>
          <CardDescription className="text-xs">Wklej link Amazon lub ASIN — automatycznie rozpoznamy marketplace i pobierzemy dane</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                value={importInput}
                onChange={(e) => handleImportChange(e.target.value)}
                placeholder="https://www.amazon.de/dp/B0XXXXXX lub B0XXXXXX"
                onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
              />
              {/* WHY: Show detected ASIN + marketplace badge inline */}
              {detectedInfo.asin && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
                  {detectedInfo.marketplace && (
                    <span className="rounded bg-blue-500/20 px-1.5 py-0.5 text-[10px] font-medium text-blue-400">
                      {detectedInfo.marketplace}
                    </span>
                  )}
                  <span className="text-[10px] font-mono text-gray-500">{detectedInfo.asin}</span>
                </div>
              )}
            </div>
            <Button
              onClick={handleFetch}
              disabled={!detectedInfo.asin || importLoading}
              variant="outline"
              size="default"
            >
              {importLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="ml-1.5">Pobierz</span>
            </Button>
          </div>

          {importError && (
            <p className="text-xs text-red-400">{importError}</p>
          )}

          {detectedInfo.type === 'asin' && !detectedInfo.marketplace && detectedInfo.asin && (
            <p className="text-[10px] text-amber-400">
              Sam ASIN bez marketplace — wklej pełny link Amazon żeby auto-wykryć kraj
            </p>
          )}
        </CardContent>
      </Card>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Twój listing</CardTitle>
          <CardDescription>Wklej tytuł, bullet points i opis do oceny</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Tytuł <span className="text-red-400">*</span>
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="np. ZULAY Premium Silicone Kitchen Utensil Set (12 Piece) - Heat Resistant..."
            />
          </div>

          {/* WHY: 5 bullets by default (Amazon standard), user can add up to 10 (Vendor) */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Bullet Points <span className="text-red-400">*</span>
            </label>
            <div className="space-y-2">
              {bullets.map((bullet, idx) => (
                <div key={idx} className="flex gap-2">
                  <span className="flex h-10 w-6 items-center justify-center text-xs text-gray-600">{idx + 1}</span>
                  <Input
                    value={bullet}
                    onChange={(e) => updateBullet(idx, e.target.value)}
                    placeholder={`Bullet point ${idx + 1}`}
                  />
                  {bullets.length > 1 && (
                    <button
                      onClick={() => removeBullet(idx)}
                      className="rounded-lg border border-gray-800 px-2 text-gray-500 hover:border-red-800 hover:text-red-400 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {bullets.length < 10 && (
              <button
                onClick={addBullet}
                className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
              >
                <Plus className="h-3 w-3" /> Dodaj bullet
              </button>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">Opis (opcjonalnie)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Wklej opis produktu do oceny (opcjonalnie — jeśli masz A+ Content lub opis HTML)"
              rows={4}
              className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
            />
          </div>
        </CardContent>
      </Card>

      {/* Score Button */}
      <Button onClick={handleScore} disabled={!canSubmit || isLoading} size="lg">
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="mr-2 h-4 w-4" />
        )}
        {isLoading ? 'Analizuję listing...' : 'Oceń listing'}
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
      {result && result.dimensions.length > 0 && (
        <div className="space-y-4">
          {/* Overall Score */}
          <Card className={cn('border', scoreBg(result.overall_score))}>
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <p className="text-sm text-gray-400">Ogólna ocena</p>
                <p className={cn('text-4xl font-bold', scoreColor(result.overall_score))}>
                  {result.overall_score.toFixed(1)}<span className="text-lg text-gray-500">/10</span>
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">
                  {result.overall_score >= 8 ? 'Świetny listing!' : result.overall_score >= 6 ? 'Dobry, ale jest potencjał' : 'Wymaga poprawy'}
                </p>
                {result.sources_used > 0 && (
                  <p className="mt-1 text-[10px] text-gray-600">
                    Na podstawie {result.sources_used} źródeł ekspertów
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Dimension cards */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {result.dimensions.map((dim, idx) => (
              <Card key={idx} className="border border-gray-800">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {scoreIcon(dim.score)}
                      <span className="text-sm font-medium text-white">{dim.name}</span>
                    </div>
                    <span className={cn('text-lg font-bold', scoreColor(dim.score))}>
                      {dim.score}
                    </span>
                  </div>
                  <ScoreBar score={dim.score} />
                  <p className="text-xs text-gray-400">{dim.explanation}</p>
                  {dim.tip && (
                    <div className="rounded-md bg-[#1A1A1A] border border-gray-800 p-2">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-600 mb-1">Wskazówka</p>
                      <p className="text-xs text-gray-300">{dim.tip}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {result && result.dimensions.length === 0 && (
        <Card>
          <CardContent className="p-6 text-center text-sm text-gray-400">
            Nie udało się ocenić listingu. Spróbuj ponownie.
          </CardContent>
        </Card>
      )}
    </div>
  )
}
