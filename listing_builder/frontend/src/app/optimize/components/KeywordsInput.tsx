// frontend/src/app/optimize/components/KeywordsInput.tsx
// Purpose: Keywords textarea + CSV/TSV import with Helium10/DataDive auto-detection
// NOT for: Keyword analysis/intel (that's KeywordIntelCard.tsx)

'use client'

import { useMemo, useState, useEffect } from 'react'
import { Hash, FileText, Upload, Lightbulb } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api/client'
import { useTier } from '@/lib/hooks/useTier'
import type { OptimizerKeyword } from '@/lib/types'

// WHY: Helium10 Cerebro = "Keyword Phrase" + "Search Volume", Magnet = "Keyword" + "Search Volume"
// DataDive = "keyword" + "search_volume" or "volume"
const KW_HEADER = /^(keyword\s*phrase|keyword|search\s*term|phrase)$/i
const VOL_HEADER = /^(search\s*volume|volume|search_volume|sv|avg\.?\s*searches)$/i

/** Parse raw CSV/TSV text into keyword,volume lines */
function parseCsvKeywords(text: string): string[] {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)
  if (lines.length === 0) return []

  const header = lines[0].toLowerCase()
  const sep = header.includes('\t') ? '\t' : ','
  const cols = header.split(sep).map((c) => c.replace(/^["']|["']$/g, '').trim())

  const kwIdx = cols.findIndex((c) => KW_HEADER.test(c))
  const volIdx = cols.findIndex((c) => VOL_HEADER.test(c))

  if (kwIdx < 0) return lines // WHY: No known header — plain text, pass through

  return lines.slice(1).map((line) => {
    const parts = line.split(sep).map((p) => p.replace(/^["']|["']$/g, '').trim())
    const kw = parts[kwIdx]
    if (!kw) return ''
    const vol = volIdx >= 0 ? parseInt(parts[volIdx]?.replace(/[,.\s]/g, '')) : NaN
    return !isNaN(vol) && vol > 0 ? `${kw},${vol}` : kw
  }).filter(Boolean)
}

/** Parse textarea lines into structured keywords */
function parseKeywordLines(text: string): OptimizerKeyword[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const commaIdx = line.lastIndexOf(',')
      if (commaIdx > 0) {
        const phrase = line.substring(0, commaIdx).trim().replace(/^["']|["']$/g, '')
        const vol = parseInt(line.substring(commaIdx + 1).trim())
        if (!isNaN(vol) && vol > 0) return { phrase, search_volume: vol }
      }
      return { phrase: line.replace(/^["']|["']$/g, ''), search_volume: 0 }
    })
}

interface KeywordsInputProps {
  value: string
  onChange: (value: string) => void
}

export default function KeywordsInput({ value, onChange }: KeywordsInputProps) {
  const { isPremium } = useTier()
  const parsedKeywords = useMemo(() => parseKeywordLines(value), [value])
  const keywordCount = parsedKeywords.length
  const [suggestions, setSuggestions] = useState<{ phrase: string; count: number }[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // WHY: Load suggestions once on mount — from user's optimization history
  useEffect(() => {
    if (!isPremium) return
    apiRequest<{ phrase: string; count: number }[]>('get', '/optimizer/keyword-suggestions', undefined, { limit: 30 })
      .then((res) => { if (res.data) setSuggestions(res.data) })
      .catch(() => {})
  }, [isPremium])

  const handleAddSuggestion = (phrase: string) => {
    // WHY: Don't add if already in textarea
    const existing = value.toLowerCase().split('\n').map((l) => l.split(',')[0].trim().toLowerCase())
    if (existing.includes(phrase.toLowerCase())) return
    onChange((value ? value + '\n' : '') + phrase)
  }

  const handleCsvImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const text = ev.target?.result as string
      if (!text) return
      const parsed = parseCsvKeywords(text)
      if (parsed.length > 0) {
        onChange((value ? value + '\n' : '') + parsed.join('\n'))
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  return (
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
          value={value}
          onChange={(e) => onChange(e.target.value)}
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

        {/* WHY: Help box — single upload entry point with tool-specific instructions */}
        <div className="mt-4 rounded-lg border border-dashed border-gray-700 bg-[#121212] p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-300">Import keywords z Helium10 / DataDive</span>
            <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-500">opcjonalnie</span>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Eksportuj CSV z dowolnego narzedzia Helium10 lub DataDive i wrzuc tutaj. System automatycznie rozpozna format i wyciagnie keywords z search volume + Ranking Juice.
          </p>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-700 py-4 text-sm text-gray-400 hover:border-gray-500 hover:text-white transition-colors">
            <Upload className="h-4 w-4" />
            Upload CSV / TSV
            <input type="file" accept=".csv,.txt,.tsv" onChange={handleCsvImport} className="hidden" />
          </label>
          <p className="mt-2 text-[10px] text-gray-600">
            Helium10: Cerebro/Magnet → Export → CSV. DataDive: Export → Download CSV.
          </p>
        </div>

        {/* Keyword suggestions from history */}
        {isPremium && suggestions.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-300"
            >
              <Lightbulb className="h-3 w-3" />
              Sugestie z historii ({suggestions.length})
            </button>
            {showSuggestions && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {suggestions.map((s) => (
                  <button
                    key={s.phrase}
                    onClick={() => handleAddSuggestion(s.phrase)}
                    className="rounded-full border border-gray-700 bg-[#1A1A1A] px-2.5 py-1 text-xs text-gray-300 hover:border-gray-500 hover:text-white transition-colors"
                  >
                    {s.phrase}
                    <span className="ml-1 text-gray-600">x{s.count}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// WHY: Export parser for SingleTab to use in canSubmit / payload building
export { parseKeywordLines }
