// frontend/src/app/demo/amazon-pro/components/CompetitorInspire.tsx
// Purpose: Input competitor ASINs → scrape → AI generates listing versions for A/B testing
// NOT for: Single competitor compliance scan (that's in StepOptimize)

'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Search, Loader2, Copy, Check, ChevronDown, ChevronUp, AlertTriangle, Sparkles, Users, X, Plus } from 'lucide-react'
import type { CompetitorInspireResult, ListingVersion, ScrapedCompetitor } from '../types'

interface CompetitorInspireProps {
  marketplace: string
  keywords?: Array<{ keyword: string; search_volume: number; ranking_juice: number }>
  onApplyVersion?: (version: ListingVersion) => void
}

const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

// WHY: LLM generates Amazon-style HTML (<b>, <br>, <ul>, <li>) in descriptions.
// Strip everything except safe tags to prevent XSS from injected competitor data.
function sanitizeHtml(html: string): string {
  return html.replace(/<(?!\/?(?:b|br|ul|li|strong|em)\b)[^>]*>/gi, '')
}

// WHY: Extract ASIN from URL or raw input (same logic as StepFetch)
function extractAsin(input: string): string {
  const trimmed = input.trim().toUpperCase()
  if (/^[B0][0-9A-Z]{9}$/.test(trimmed)) return trimmed
  const match = trimmed.match(/(?:\/DP\/|\/GP\/PRODUCT\/)([B0][0-9A-Z]{9})/)
  if (match) return match[1]
  return trimmed
}

// WHY: Tab component for version switching
const VERSION_COLORS = ['text-blue-400 border-blue-400', 'text-green-400 border-green-400', 'text-amber-400 border-amber-400']
const VERSION_BG = ['bg-blue-500/10', 'bg-green-500/10', 'bg-amber-500/10']

export default function CompetitorInspire({ marketplace, keywords, onApplyVersion }: CompetitorInspireProps) {
  const [asins, setAsins] = useState<string[]>(['', ''])
  const [showCompetitors, setShowCompetitors] = useState(false)
  const [activeVersion, setActiveVersion] = useState(0)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const inspireMutation = useMutation({
    mutationFn: async (useSample?: boolean) => {
      const lang = marketplace === 'DE' ? 'de' : marketplace === 'PL' ? 'pl' : marketplace === 'FR' ? 'fr' : 'en'
      if (useSample) {
        const { data } = await apiClient.post<CompetitorInspireResult>('/demo/competitor-inspire', {
          use_sample: true, marketplace, language: lang,
          keywords: keywords || [],
        })
        if (data.error) throw new Error(data.error)
        return data
      }
      const validAsins = asins.map(extractAsin).filter(a => /^[B0][0-9A-Z]{9}$/.test(a))
      if (validAsins.length < 2) throw new Error('Podaj minimum 2 ASINy konkurentów')
      const { data } = await apiClient.post<CompetitorInspireResult>('/demo/competitor-inspire', {
        asins: validAsins, marketplace, language: lang,
        keywords: keywords || [],
      })
      if (data.error) throw new Error(data.error)
      return data
    },
  })

  const addAsin = () => {
    if (asins.length < 5) setAsins([...asins, ''])
  }

  const removeAsin = (idx: number) => {
    if (asins.length > 2) setAsins(asins.filter((_, i) => i !== idx))
  }

  const updateAsin = (idx: number, value: string) => {
    const updated = [...asins]
    updated[idx] = value
    setAsins(updated)
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const result = inspireMutation.data
  const versions = result?.versions || []
  const current = versions[activeVersion]

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Users className="w-5 h-5 text-blue-400" />
        <h3 className="text-base font-semibold text-white">Competitor-Inspired Generator</h3>
      </div>
      <p className="text-xs text-gray-500">
        Podaj ASINy konkurentów — system pobierze ich listingi, połączy z Twoimi keywords{keywords && keywords.length > 0 ? ` (${keywords.length} załadowanych)` : ''} i wygeneruje 3 wersje do testowania.
      </p>

      {/* ASIN inputs */}
      {!result && (
        <div className="space-y-2">
          {asins.map((asin, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-xs text-gray-600 w-4">{idx + 1}.</span>
              <input
                type="text"
                value={asin}
                onChange={(e) => updateAsin(idx, e.target.value)}
                placeholder={`ASIN lub URL konkurenta ${idx + 1}`}
                className={inputCls}
              />
              {asins.length > 2 && (
                <button onClick={() => removeAsin(idx)} className="text-gray-600 hover:text-red-400">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}

          <div className="flex items-center gap-3">
            {asins.length < 5 && (
              <button onClick={addAsin} className="flex items-center gap-1 text-xs text-gray-500 hover:text-white">
                <Plus className="w-3.5 h-3.5" /> Dodaj ASIN
              </button>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => inspireMutation.mutate(false)}
              disabled={inspireMutation.isPending || asins.filter(a => a.trim()).length < 2}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-40 transition-colors"
            >
              {inspireMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generuję 3 wersje...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analizuj i generuj
                </>
              )}
            </button>
            <button
              onClick={() => inspireMutation.mutate(true)}
              disabled={inspireMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-2.5 text-xs text-gray-400 hover:text-white hover:border-gray-500 disabled:opacity-40 transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              Demo
            </button>
          </div>

          {inspireMutation.error && (
            <p className="text-xs text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {(inspireMutation.error as Error).message}
            </p>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Competitors scraped */}
          <div>
            <button
              onClick={() => setShowCompetitors(!showCompetitors)}
              className="flex items-center gap-2 text-xs text-gray-400 hover:text-white"
            >
              {showCompetitors ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {result.competitors.length} listingów pobranych
              {result.failed.length > 0 && (
                <span className="text-red-400">({result.failed.length} błędów)</span>
              )}
            </button>

            {showCompetitors && (
              <div className="mt-2 space-y-2">
                {result.competitors.map((c: ScrapedCompetitor) => (
                  <div key={c.asin} className="border border-gray-800 rounded-lg p-3 bg-[#121212]">
                    <p className="text-xs text-gray-500 font-mono">{c.asin}</p>
                    <p className="text-sm text-white mt-1 line-clamp-2">{c.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{c.bullets.length} bullets</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Common keywords */}
          {result.common_keywords.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1.5">Top keywords z konkurencji:</p>
              <div className="flex flex-wrap gap-1.5">
                {result.common_keywords.slice(0, 15).map((kw: string, i: number) => (
                  <span key={i} className="text-[11px] bg-gray-800 text-gray-400 rounded px-2 py-0.5">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Version tabs */}
          {versions.length > 0 && (
            <div>
              <div className="flex gap-1 border-b border-gray-800">
                {versions.map((v: ListingVersion, i: number) => (
                  <button
                    key={i}
                    onClick={() => setActiveVersion(i)}
                    className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                      activeVersion === i
                        ? VERSION_COLORS[i]
                        : 'text-gray-600 border-transparent hover:text-gray-400'
                    }`}
                  >
                    {v.name}
                  </button>
                ))}
              </div>

              {/* Active version content */}
              {current && (
                <div className={`mt-3 space-y-3 rounded-xl p-4 border border-gray-800 ${VERSION_BG[activeVersion]}`}>
                  {/* Title */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-500 uppercase tracking-wide">Tytuł</span>
                      <button
                        onClick={() => copyToClipboard(current.title, `title-${activeVersion}`)}
                        className="text-gray-600 hover:text-white"
                      >
                        {copiedField === `title-${activeVersion}` ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-sm text-white leading-relaxed">{current.title}</p>
                    <p className="text-[10px] text-gray-600 mt-0.5">{current.title.length} znaków</p>
                  </div>

                  {/* Bullets */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-500 uppercase tracking-wide">Bullet Points</span>
                      <button
                        onClick={() => copyToClipboard(current.bullets.join('\n'), `bullets-${activeVersion}`)}
                        className="text-gray-600 hover:text-white"
                      >
                        {copiedField === `bullets-${activeVersion}` ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <ul className="space-y-1.5">
                      {current.bullets.filter((b: string) => b.trim()).map((b: string, i: number) => (
                        <li key={i} className="text-xs text-gray-300 leading-relaxed pl-3 border-l-2 border-gray-700">
                          {b}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Description */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-500 uppercase tracking-wide">Opis</span>
                      <button
                        onClick={() => copyToClipboard(current.description, `desc-${activeVersion}`)}
                        className="text-gray-600 hover:text-white"
                      >
                        {copiedField === `desc-${activeVersion}` ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <div className="text-xs text-gray-300 leading-relaxed [&_b]:font-semibold [&_ul]:list-disc [&_ul]:pl-4 [&_li]:mt-1" dangerouslySetInnerHTML={{ __html: sanitizeHtml(current.description) }} />
                  </div>

                  {/* Backend keywords */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-500 uppercase tracking-wide">Backend Keywords</span>
                      <button
                        onClick={() => copyToClipboard(current.backend_keywords, `bk-${activeVersion}`)}
                        className="text-gray-600 hover:text-white"
                      >
                        {copiedField === `bk-${activeVersion}` ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-[11px] text-gray-500 font-mono break-all">{current.backend_keywords}</p>
                  </div>

                  {/* Apply button */}
                  {onApplyVersion && (
                    <button
                      onClick={() => onApplyVersion(current)}
                      className="w-full mt-2 rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/20 transition-colors"
                    >
                      Użyj tej wersji
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Reset */}
          <button
            onClick={() => {
              inspireMutation.reset()
              setAsins(['', ''])
              setActiveVersion(0)
            }}
            className="text-xs text-gray-600 hover:text-white"
          >
            Spróbuj z innymi ASINami
          </button>
        </div>
      )}
    </div>
  )
}
