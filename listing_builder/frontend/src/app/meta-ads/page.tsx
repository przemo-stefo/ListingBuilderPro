// frontend/src/app/meta-ads/page.tsx
// Purpose: Meta Ads Studio — 4-tab interface for ad copy, headlines, video hooks, creative briefs
// NOT for: Old ad-copy page (/ad-copy/page.tsx) or listing optimization

'use client'

import { useState } from 'react'
import {
  Megaphone, Loader2, Plus, X, Copy, Check, Sparkles,
  Type, Video, FileText,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'adcopy', label: 'Ad Copy', icon: Megaphone, desc: 'Generuj 3 warianty reklam' },
  { id: 'headlines', label: 'Headlines', icon: Type, desc: '10 nagłówków wg formuł' },
  { id: 'hooks', label: 'Video Hooks', icon: Video, desc: '5 hooków 3-elementowych' },
  { id: 'brief', label: 'Creative Brief', icon: FileText, desc: 'Brief kreatywny 11-krokowy' },
] as const

type TabId = (typeof TABS)[number]['id']

const PLATFORMS = [
  { id: 'facebook', label: 'Facebook', emoji: 'FB' },
  { id: 'instagram', label: 'Instagram', emoji: 'IG' },
  { id: 'tiktok', label: 'TikTok', emoji: 'TT' },
]

const FRAMEWORKS = [
  { id: 'mixed', label: 'Mix (Hook/Story/Benefit)' },
  { id: 'aida', label: 'AIDA' },
  { id: 'pas', label: 'PAS' },
]

const VARIATION_STYLES: Record<string, { border: string; bg: string; label: string; accent: string }> = {
  hook: { border: 'border-amber-800', bg: 'bg-amber-900/20', label: 'Hook', accent: 'text-amber-400' },
  story: { border: 'border-blue-800', bg: 'bg-blue-900/20', label: 'Story', accent: 'text-blue-400' },
  benefit: { border: 'border-green-800', bg: 'bg-green-900/20', label: 'Benefit', accent: 'text-green-400' },
  aida_curiosity: { border: 'border-purple-800', bg: 'bg-purple-900/20', label: 'AIDA Curiosity', accent: 'text-purple-400' },
  aida_pain: { border: 'border-red-800', bg: 'bg-red-900/20', label: 'AIDA Pain', accent: 'text-red-400' },
  aida_social: { border: 'border-cyan-800', bg: 'bg-cyan-900/20', label: 'AIDA Social', accent: 'text-cyan-400' },
  pas_emotional: { border: 'border-pink-800', bg: 'bg-pink-900/20', label: 'PAS Emotional', accent: 'text-pink-400' },
  pas_logical: { border: 'border-teal-800', bg: 'bg-teal-900/20', label: 'PAS Logical', accent: 'text-teal-400' },
  pas_story: { border: 'border-orange-800', bg: 'bg-orange-900/20', label: 'PAS Story', accent: 'text-orange-400' },
}

const AWARENESS_COLORS: Record<string, string> = {
  unaware: 'bg-gray-700 text-gray-300',
  problem_aware: 'bg-red-900/40 text-red-400',
  solution_aware: 'bg-amber-900/40 text-amber-400',
  product_aware: 'bg-blue-900/40 text-blue-400',
  most_aware: 'bg-green-900/40 text-green-400',
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AdVariation {
  type: string
  headline: string
  primary_text: string
  description: string
}

interface Headline {
  headline: string
  formula: string
  awareness_stage: string
}

interface VideoHook {
  angle: string
  visual: string
  caption: string
  verbal: string
  why_it_works: string
}

interface CreativeBrief {
  icp: string
  pain_points: string[]
  desires: string[]
  hesitations: string[]
  unique_mechanism: string
  proof_elements: string[]
  creative_angles: { angle: string; description: string }[]
  recommended_formats: { angle: string; formats: string[] }[]
  copy_hooks: { angle: string; hooks: string[] }[]
  cta_strategy: string
  testing_plan: string
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function MetaAdsStudioPage() {
  const [activeTab, setActiveTab] = useState<TabId>('adcopy')
  const [productTitle, setProductTitle] = useState('')
  const [features, setFeatures] = useState<string[]>([''])
  const [targetAudience, setTargetAudience] = useState('')
  const [platform, setPlatform] = useState('facebook')
  const [framework, setFramework] = useState('mixed')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copiedField, setCopiedField] = useState<string | null>(null)

  // WHY: Separate result state per tab — switching tabs preserves results
  const [adResult, setAdResult] = useState<{ variations: AdVariation[]; sources: string[] } | null>(null)
  const [headlineResult, setHeadlineResult] = useState<{ headlines: Headline[]; sources: string[] } | null>(null)
  const [hookResult, setHookResult] = useState<{ hooks: VideoHook[]; sources: string[] } | null>(null)
  const [briefResult, setBriefResult] = useState<{ brief: CreativeBrief; sources: string[] } | null>(null)

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
  const copyText = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const handleGenerate = async () => {
    if (!canSubmit || isLoading) return
    setIsLoading(true)
    setError('')

    const productPayload = {
      product_title: productTitle,
      product_features: validFeatures,
      target_audience: targetAudience || undefined,
    }

    try {
      if (activeTab === 'adcopy') {
        const { data } = await apiClient.post('/ads/generate', { ...productPayload, platform, framework })
        setAdResult({ variations: data.variations, sources: data.sources || [] })
      } else if (activeTab === 'headlines') {
        const { data } = await apiClient.post('/ads/headlines', productPayload)
        setHeadlineResult({ headlines: data.headlines, sources: data.sources || [] })
      } else if (activeTab === 'hooks') {
        const { data } = await apiClient.post('/ads/hooks', productPayload)
        setHookResult({ hooks: data.hooks, sources: data.sources || [] })
      } else if (activeTab === 'brief') {
        const { data } = await apiClient.post('/ads/brief', productPayload)
        setBriefResult({ brief: data.brief, sources: data.sources || [] })
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nieznany błąd')
    } finally {
      setIsLoading(false)
    }
  }

  const generateLabel: Record<TabId, string> = {
    adcopy: 'Generuj reklamy',
    headlines: 'Generuj nagłówki',
    hooks: 'Generuj hooki',
    brief: 'Generuj brief',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-amber-500/20 p-2">
          <Megaphone className="h-6 w-6 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Meta Ads Studio</h1>
          <p className="text-xs text-gray-400">Reklamy, nagłówki, hooki video i briefy kreatywne AI</p>
        </div>
        <span className="ml-auto rounded bg-amber-900/40 px-2 py-0.5 text-xs font-bold text-amber-400">BETA</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#1A1A1A] p-1">
        {TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 rounded-md px-4 py-2 text-sm transition-colors flex-1 justify-center',
                activeTab === tab.id
                  ? 'bg-white/10 text-white font-medium'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Product Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dane produktu</CardTitle>
          <CardDescription>Podaj informacje o produkcie</CardDescription>
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

          {/* WHY: Platform + framework only relevant for adcopy tab */}
          {activeTab === 'adcopy' && (
            <>
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

              <div>
                <label className="mb-2 block text-sm text-gray-400">Framework copywriterski</label>
                <div className="flex gap-2">
                  {FRAMEWORKS.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setFramework(f.id)}
                      className={cn(
                        'rounded-lg border px-4 py-2 text-sm transition-colors',
                        framework === f.id
                          ? 'border-white bg-white/5 text-white'
                          : 'border-gray-800 text-gray-400 hover:border-gray-600'
                      )}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Generate Button */}
      <Button onClick={handleGenerate} disabled={!canSubmit || isLoading} size="lg">
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="mr-2 h-4 w-4" />
        )}
        {isLoading ? 'Generowanie...' : generateLabel[activeTab]}
      </Button>

      {/* Error */}
      {error && (
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results — Ad Copy Tab */}
      {activeTab === 'adcopy' && adResult && (
        <div className="space-y-4">
          <SourceBadges sources={adResult.sources} />
          {adResult.variations.map((v, idx) => {
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
                  <CopyField label="Nagłówek" text={v.headline} field={`h-${idx}`} copied={copiedField} onCopy={copyText} bold />
                  <CopyField label="Tekst główny" text={v.primary_text} field={`p-${idx}`} copied={copiedField} onCopy={copyText} />
                  <CopyField label="Opis" text={v.description} field={`d-${idx}`} copied={copiedField} onCopy={copyText} muted />
                  <CopyAllButton text={`${v.headline}\n\n${v.primary_text}\n\n${v.description}`} field={`all-${idx}`} copied={copiedField} onCopy={copyText} />
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Results — Headlines Tab */}
      {activeTab === 'headlines' && headlineResult && (
        <div className="space-y-4">
          <SourceBadges sources={headlineResult.sources} />
          <Card>
            <CardContent className="divide-y divide-gray-800 p-0">
              {headlineResult.headlines.map((h, idx) => (
                <div key={idx} className="flex items-start justify-between gap-4 p-4">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{h.headline}</p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="text-[10px] text-gray-500">Formula: {h.formula}</span>
                      <span className={cn('rounded px-1.5 py-0.5 text-[10px] font-medium', AWARENESS_COLORS[h.awareness_stage] || 'bg-gray-800 text-gray-400')}>
                        {h.awareness_stage?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <button onClick={() => copyText(h.headline, `hl-${idx}`)} className="text-gray-600 hover:text-white transition-colors mt-1">
                    {copiedField === `hl-${idx}` ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results — Video Hooks Tab */}
      {activeTab === 'hooks' && hookResult && (
        <div className="space-y-4">
          <SourceBadges sources={hookResult.sources} />
          {hookResult.hooks.map((h, idx) => (
            <Card key={idx} className="border-gray-800">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-blue-900/30 px-2 py-0.5 text-xs font-bold text-blue-400">
                    {h.angle}
                  </span>
                  <CardTitle className="text-base text-white">Hook {idx + 1}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-amber-500">Visual</p>
                    <p className="text-xs text-gray-300">{h.visual}</p>
                  </div>
                  <div className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-green-500">Caption</p>
                    <p className="text-xs text-gray-300">{h.caption}</p>
                  </div>
                  <div className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-blue-500">Verbal</p>
                    <p className="text-xs text-gray-300">{h.verbal}</p>
                  </div>
                </div>
                <p className="text-xs italic text-gray-500">{h.why_it_works}</p>
                <CopyAllButton
                  text={`VISUAL: ${h.visual}\nCAPTION: ${h.caption}\nVERBAL: ${h.verbal}`}
                  field={`hook-all-${idx}`}
                  copied={copiedField}
                  onCopy={copyText}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Results — Creative Brief Tab */}
      {activeTab === 'brief' && briefResult && (
        <div className="space-y-4">
          <SourceBadges sources={briefResult.sources} />
          <Card>
            <CardContent className="space-y-6 pt-6">
              <BriefSection title="ICP (Ideal Customer Profile)" content={briefResult.brief.icp} />
              <BriefList title="Top Pain Points" items={briefResult.brief.pain_points} color="text-red-400" />
              <BriefList title="Top Desires" items={briefResult.brief.desires} color="text-green-400" />
              <BriefList title="Key Hesitations" items={briefResult.brief.hesitations} color="text-amber-400" />
              <BriefSection title="Unique Mechanism" content={briefResult.brief.unique_mechanism} />
              <BriefList title="Proof Elements" items={briefResult.brief.proof_elements} color="text-blue-400" />

              {briefResult.brief.creative_angles && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-white">Creative Angles</h3>
                  <div className="grid gap-2 sm:grid-cols-3">
                    {briefResult.brief.creative_angles.map((a, i) => (
                      <div key={i} className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
                        <p className="text-xs font-bold text-cyan-400">{a.angle}</p>
                        <p className="mt-1 text-xs text-gray-400">{a.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {briefResult.brief.copy_hooks && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-white">Copy Hooks</h3>
                  {briefResult.brief.copy_hooks.map((ch, i) => (
                    <div key={i} className="mb-2">
                      <p className="text-xs font-medium text-gray-400 mb-1">{ch.angle}:</p>
                      <ul className="space-y-0.5 pl-4">
                        {ch.hooks.map((hook, j) => (
                          <li key={j} className="text-xs text-gray-300 list-disc">{hook}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}

              <BriefSection title="CTA Strategy" content={briefResult.brief.cta_strategy} />
              <BriefSection title="Testing Plan" content={briefResult.brief.testing_plan} />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SourceBadges({ sources }: { sources: string[] }) {
  if (!sources.length) return null
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
      <span>Wykorzystano {sources.length} źródeł wiedzy:</span>
      {sources.map((s, i) => (
        <span key={i} className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400">{s}</span>
      ))}
    </div>
  )
}

function CopyField({
  label, text, field, copied, onCopy, bold, muted,
}: {
  label: string
  text: string
  field: string
  copied: string | null
  onCopy: (text: string, field: string) => void
  bold?: boolean
  muted?: boolean
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">{label}</span>
        <button onClick={() => onCopy(text, field)} className="text-gray-600 hover:text-white transition-colors">
          {copied === field ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
        </button>
      </div>
      <p className={cn('text-sm whitespace-pre-wrap', bold ? 'font-semibold text-white' : muted ? 'text-gray-400' : 'text-gray-300')}>
        {text}
      </p>
    </div>
  )
}

function CopyAllButton({
  text, field, copied, onCopy,
}: {
  text: string
  field: string
  copied: string | null
  onCopy: (text: string, field: string) => void
}) {
  return (
    <button
      onClick={() => onCopy(text, field)}
      className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-white transition-colors pt-1"
    >
      {copied === field ? (
        <><Check className="h-3 w-3 text-green-400" /> Skopiowano!</>
      ) : (
        <><Copy className="h-3 w-3" /> Kopiuj całość</>
      )}
    </button>
  )
}

function BriefSection({ title, content }: { title: string; content: string }) {
  if (!content) return null
  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-white">{title}</h3>
      <p className="text-xs text-gray-300 whitespace-pre-wrap">{content}</p>
    </div>
  )
}

function BriefList({ title, items, color }: { title: string; items: string[]; color: string }) {
  if (!items?.length) return null
  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-white">{title}</h3>
      <ul className="space-y-0.5 pl-4">
        {items.map((item, i) => (
          <li key={i} className={cn('text-xs list-disc', color)}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
