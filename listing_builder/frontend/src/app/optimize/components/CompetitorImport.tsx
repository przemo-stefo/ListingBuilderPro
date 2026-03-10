// frontend/src/app/optimize/components/CompetitorImport.tsx
// Purpose: Paste ASIN/URL → fetch competitor listing → pre-fill optimizer form
// NOT for: Competitor price tracking (competitors_routes), listing scoring (listing_score_routes)

'use client'

import { useState } from 'react'
import { Search, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiRequest } from '@/lib/api/client'

interface FetchResponse {
  asin: string
  marketplace: string
  title: string
  bullets: string[]
  description: string
  a_plus_content: string
  url: string
  error: string
}

interface CompetitorImportProps {
  onImport: (data: {
    title: string
    asin: string
    marketplace: string
    bullets: string[]
    description: string
  }) => void
}

export function CompetitorImport({ onImport }: CompetitorImportProps) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fetched, setFetched] = useState<FetchResponse | null>(null)

  const handleFetch = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    setLoading(true)
    setError('')
    setFetched(null)
    try {
      const res = await apiRequest<FetchResponse>('post', '/score/fetch', { input: trimmed })
      if (res.error) {
        setError(res.error)
        return
      }
      const data = res.data!
      if (data.error) {
        setError(data.error)
        return
      }
      if (!data.title) {
        setError('Nie udalo sie pobrac listingu — sprobuj wkleic dane recznie')
        return
      }
      setFetched(data)
    } catch {
      setError('Blad polaczenia z serwerem')
    } finally {
      setLoading(false)
    }
  }

  const handleUseData = () => {
    if (!fetched) return
    onImport({
      title: fetched.title,
      asin: fetched.asin,
      marketplace: fetched.marketplace,
      bullets: fetched.bullets,
      description: fetched.description,
    })
    setFetched(null)
    setInput('')
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-lg">Import listingu konkurencji</CardTitle>
        </div>
        <p className="text-sm text-gray-500">
          Wklej ASIN lub link Amazon — pobierzemy tytul, bullet points i opis do porownania.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="B0DXXXXXX lub https://www.amazon.de/dp/B0DXXXXXX"
            onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
          />
          <Button onClick={handleFetch} disabled={loading || !input.trim()} className="shrink-0">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Pobierz'}
          </Button>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        {fetched && (
          <div className="rounded-lg border border-gray-800 bg-[#121212] p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                {fetched.asin} · {fetched.marketplace}
              </span>
              {fetched.url && (
                <a href={fetched.url} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-500 hover:text-gray-300">
                  <ExternalLink className="inline h-3 w-3" />
                </a>
              )}
            </div>
            <p className="text-sm font-medium text-white line-clamp-2">{fetched.title}</p>
            {fetched.bullets.length > 0 && (
              <ul className="text-xs text-gray-400 space-y-0.5">
                {fetched.bullets.slice(0, 3).map((b, i) => (
                  <li key={i} className="truncate">• {b}</li>
                ))}
                {fetched.bullets.length > 3 && (
                  <li className="text-gray-600">+{fetched.bullets.length - 3} wiecej...</li>
                )}
              </ul>
            )}
            <Button size="sm" variant="outline" onClick={handleUseData} className="mt-2">
              Uzyj jako dane wejsciowe
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
