// frontend/src/app/research/page.tsx
// Purpose: Audience research page — OV Skills via n8n webhook (Groq free tier)
// NOT for: Listing optimization or Expert Q&A (those are /optimize and /expert-qa)

'use client'

import { useState } from 'react'
import { Loader2, Users, Target, Lightbulb, Megaphone, PenTool, Video, Mail, Rocket, Search, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface ResearchResult {
  skill: string
  product: string
  audience: string
  result: string
  tokens_used: number
  model: string
  cost: string
}

// WHY: Skills map — n8n OV Skills workflow supports 10 skills, grouped by category
const SKILLS = [
  {
    category: 'Badanie rynku',
    items: [
      { id: 'deep-customer-research', label: 'Badanie klienta', icon: Users, desc: 'Symuluje 12 pytań badawczych jako grupa docelowa — pain points, motywacje, język kupujących' },
      { id: 'icp-discovery', label: 'Odkrywanie ICP', icon: Target, desc: 'Testuje produkt na 6 segmentach — scoring, ranking, najlepsza grupa docelowa' },
      { id: 'idea-validation', label: 'Walidacja pomysłu', icon: Rocket, desc: 'Brutalna ocena pomysłu — Go/Pivot/Kill z matrycą dowodów' },
    ],
  },
  {
    category: 'Kreacja',
    items: [
      { id: 'creative-brief', label: 'Brief kreatywny', icon: Lightbulb, desc: 'Brief strategiczny z insightem, single-minded message i tone guidance' },
      { id: 'creative-testing', label: 'Test kreacji', icon: Search, desc: 'Symuluje reakcje grupy docelowej na koncepty PRZED wydaniem budżetu' },
    ],
  },
  {
    category: 'Reklamy',
    items: [
      { id: 'facebook-ad-copy', label: 'Facebook/Instagram', icon: Megaphone, desc: '14 wariantów reklam: pain point, benefit, social proof, story, urgency' },
      { id: 'google-ad-copy', label: 'Google Ads RSA', icon: PenTool, desc: '15 nagłówków + 4 opisy z limitem znaków i Quality Score checklistą' },
      { id: 'video-script', label: 'Skrypt wideo', icon: Video, desc: 'Skrypt z timingiem, 3 hooki, pacing guide — TikTok/YouTube/UGC' },
      { id: 'email-campaign', label: 'Email kampania', icon: Mail, desc: '15 subject lines + 5 wariantów maila z A/B planem' },
    ],
  },
]

// WHY: Extra fields only for skills that need them (n8n extracts per-skill)
const EXTRA_FIELDS: Record<string, { key: string; label: string; placeholder: string }[]> = {
  'icp-discovery': [{ key: 'price', label: 'Cena', placeholder: 'np. 49 PLN, $29.99' }],
  'idea-validation': [{ key: 'price', label: 'Cena', placeholder: 'np. 49 PLN/mies' }],
  'creative-brief': [{ key: 'objective', label: 'Cel', placeholder: 'np. conversion, awareness, lead gen' }],
  'creative-testing': [{ key: 'objective', label: 'Cel', placeholder: 'np. conversion' }],
  'facebook-ad-copy': [
    { key: 'objective', label: 'Cel', placeholder: 'np. conversions, leads, traffic' },
    { key: 'offer', label: 'Oferta', placeholder: 'np. -20% z kodem LAUNCH, darmowa dostawa' },
  ],
  'google-ad-copy': [{ key: 'keywords', label: 'Słowa kluczowe', placeholder: 'np. organic dog treats, healthy snacks for dogs' }],
  'email-campaign': [{ key: 'offer', label: 'Oferta', placeholder: 'np. darmowy trial, -30% na start' }],
}

export default function ResearchPage() {
  const [selectedSkill, setSelectedSkill] = useState('deep-customer-research')
  const [product, setProduct] = useState('')
  const [audience, setAudience] = useState('')
  const [extras, setExtras] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ResearchResult | null>(null)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!product.trim() || isLoading) return
    setError('')
    setResult(null)
    setIsLoading(true)

    try {
      const body: Record<string, string> = {
        skill: selectedSkill,
        product: product.trim(),
        audience: audience.trim(),
      }
      // WHY: Only pass non-empty extras to keep payload clean
      const fields = EXTRA_FIELDS[selectedSkill] || []
      for (const f of fields) {
        if (extras[f.key]?.trim()) {
          body[f.key] = extras[f.key].trim()
        }
      }

      const res = await fetch('/api/proxy/research/audience', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Błąd ${res.status}`)
      }

      setResult(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nieznany błąd')
    } finally {
      setIsLoading(false)
    }
  }

  const currentSkillInfo = SKILLS.flatMap(c => c.items).find(s => s.id === selectedSkill)
  const extraFields = EXTRA_FIELDS[selectedSkill] || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-blue-500/20 p-2">
          <Users className="h-6 w-6 text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Badanie rynku AI</h1>
          <p className="text-xs text-gray-400">Original Voices — 10 skilli badawczych opartych na Groq AI (darmowe)</p>
        </div>
      </div>

      {/* Skill selector */}
      <div className="space-y-3">
        {SKILLS.map(category => (
          <div key={category.category}>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
              {category.category}
            </p>
            <div className="flex flex-wrap gap-2">
              {category.items.map(skill => {
                const Icon = skill.icon
                const isActive = selectedSkill === skill.id
                return (
                  <button
                    key={skill.id}
                    onClick={() => { setSelectedSkill(skill.id); setExtras({}) }}
                    className={cn(
                      'group relative flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-colors',
                      isActive
                        ? 'border-blue-600 bg-blue-900/30 text-blue-300'
                        : 'border-gray-800 bg-[#1A1A1A] text-gray-400 hover:border-gray-600 hover:text-white'
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {skill.label}
                    {/* WHY: Tooltip on hover — shows full description */}
                    <div className="pointer-events-none absolute bottom-full left-0 z-50 mb-2 hidden w-64 rounded-lg border border-gray-700 bg-[#1A1A1A] p-3 text-xs text-gray-300 shadow-xl group-hover:block">
                      {skill.desc}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Form */}
      <div className="rounded-lg border border-gray-800 bg-[#121212] p-4 space-y-3">
        {currentSkillInfo && (
          <p className="text-xs text-gray-500">{currentSkillInfo.desc}</p>
        )}

        <div>
          <label className="mb-1 block text-xs text-gray-400">Produkt / usługa *</label>
          <input
            type="text"
            value={product}
            onChange={e => setProduct(e.target.value)}
            placeholder="np. organiczne przysmaki dla psów, kurs e-commerce, aplikacja do budżetowania"
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-blue-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs text-gray-400">Grupa docelowa (opcjonalnie)</label>
          <input
            type="text"
            value={audience}
            onChange={e => setAudience(e.target.value)}
            placeholder="np. właściciele psów 30-50 lat, sprzedawcy Amazon, freelancerzy"
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-blue-800"
          />
        </div>

        {/* WHY: Dynamic extra fields based on selected skill */}
        {extraFields.map(f => (
          <div key={f.key}>
            <label className="mb-1 block text-xs text-gray-400">{f.label} (opcjonalnie)</label>
            <input
              type="text"
              value={extras[f.key] || ''}
              onChange={e => setExtras(prev => ({ ...prev, [f.key]: e.target.value }))}
              placeholder={f.placeholder}
              className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-blue-800"
            />
          </div>
        ))}

        <Button
          onClick={handleSubmit}
          disabled={!product.trim() || isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analizuje... (do 90s)
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Uruchom badanie
            </>
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-900 bg-red-900/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="rounded-lg border border-gray-800 bg-[#121212] p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-400" />
              <h2 className="text-sm font-bold text-white">Wynik badania</h2>
            </div>
            <div className="flex gap-2 text-[10px] text-gray-500">
              <span>{result.model}</span>
              <span>{result.tokens_used} tokenów</span>
              <span>{result.cost}</span>
            </div>
          </div>

          {/* WHY: pre-wrap preserves LLM formatting (numbered lists, headers, etc.) */}
          <div className="whitespace-pre-wrap text-sm text-gray-200 leading-relaxed">
            {result.result}
          </div>
        </div>
      )}
    </div>
  )
}
