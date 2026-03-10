// frontend/src/app/optimize/components/ImageGenerator.tsx
// Purpose: UI for generating AI-powered product infographics (A+ Content images)
// NOT for: Product photo upload or editing

'use client'

import { useState } from 'react'
import { ImageIcon, Loader2, Download, Sun, Moon } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'
import type { LLMProvider } from '@/lib/types'

const IMAGE_TYPE_LABELS: Record<string, { label: string; desc: string }> = {
  hero_banner: { label: 'Baner glowny', desc: 'Nagłówek A+ Content z hasłem reklamowym' },
  feature_grid: { label: 'Siatka cech', desc: '6 kluczowych cech produktu w czytelnym układzie' },
  comparison: { label: 'Tabela porównawcza', desc: 'Twój produkt vs konkurencja' },
  specs: { label: 'Specyfikacja', desc: 'Parametry techniczne w przejrzystej formie' },
}

interface ImageGeneratorProps {
  productName: string
  brand: string
  bulletPoints: string[]
  description: string
  category?: string
  language?: string
}

interface ImageResult {
  images: Record<string, string>
  image_types: string[]
  llm_provider: string
}

export default function ImageGenerator({
  productName,
  brand,
  bulletPoints,
  description,
  category = '',
  language = 'pl',
}: ImageGeneratorProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ImageResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [theme, setTheme] = useState<string>('dark_premium')
  const [provider, setProvider] = useState<LLMProvider>('beast')

  const canGenerate = productName.length >= 3 && brand.length >= 1

  const handleGenerate = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const { data } = await apiClient.post<ImageResult>('/images/generate', {
        product_name: productName,
        brand,
        bullet_points: bulletPoints,
        description,
        category,
        language,
        theme,
        llm_provider: provider,
      })
      setResult(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Generowanie grafik nie powiodlo sie'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = (imageType: string, base64Data: string) => {
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${base64Data}`
    link.download = `${brand.toLowerCase()}-${imageType}.png`
    link.click()
  }

  const handleDownloadAll = () => {
    if (!result) return
    for (const type of result.image_types) {
      if (result.images[type]) {
        setTimeout(() => handleDownload(type, result.images[type]), 200)
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-lg">Grafiki A+ Content</CardTitle>
        </div>
        <CardDescription>
          Wygeneruj profesjonalne infografiki do Amazon A+ Content. AI analizuje Twoj produkt i tworzy: baner, siatke cech, tabele porownawcza i specyfikacje.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Theme toggle */}
          <div className="flex items-center gap-1 rounded-lg border border-gray-800 p-1">
            {[
              { id: 'dark_premium', icon: Moon, label: 'Premium' },
              { id: 'light_clean', icon: Sun, label: 'Light' },
              { id: 'amazon_white', icon: Sun, label: 'Amazon' },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={cn(
                  'flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors',
                  theme === t.id ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-300'
                )}
              >
                <t.icon className="h-3 w-3" /> {t.label}
              </button>
            ))}
          </div>

          {/* Provider picker — Beast preferred (free/unlimited) */}
          <div className="flex items-center gap-1 rounded-lg border border-gray-800 p-1">
            {(['beast', 'groq'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setProvider(p)}
                className={cn(
                  'rounded px-2 py-1 text-xs transition-colors',
                  provider === p ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-300'
                )}
              >
                {p === 'beast' ? 'Beast AI' : 'Groq'}
              </button>
            ))}
          </div>

          {/* Generate button */}
          <Button
            onClick={handleGenerate}
            disabled={!canGenerate || isLoading}
            size="sm"
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ImageIcon className="mr-2 h-4 w-4" />
            )}
            {isLoading ? 'Generowanie...' : 'Generuj grafiki'}
          </Button>

          {result && (
            <Button onClick={handleDownloadAll} variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Pobierz wszystkie
            </Button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-800/50 bg-red-900/20 p-3">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            <p className="text-sm text-gray-500">AI analizuje produkt i generuje grafiki...</p>
            <p className="text-xs text-gray-600">To moze potrwac 15-30 sekund</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>Wygenerowano {result.image_types.length} grafik</span>
              <span>•</span>
              <span>Model: {result.llm_provider === 'beast' ? 'Beast AI (Qwen3 235B)' : 'Groq (Llama 3.3)'}</span>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {result.image_types.map((type) => {
                const meta = IMAGE_TYPE_LABELS[type] || { label: type, desc: '' }
                const base64 = result.images[type]
                if (!base64) return null

                return (
                  <div key={type} className="group rounded-lg border border-gray-800 bg-[#121212] overflow-hidden">
                    {/* Image preview */}
                    <div className="relative bg-[#0D1117]">
                      <img
                        src={`data:image/png;base64,${base64}`}
                        alt={meta.label}
                        className="w-full h-auto"
                      />
                      {/* Download overlay */}
                      <button
                        onClick={() => handleDownload(type, base64)}
                        className="absolute right-2 top-2 rounded-lg bg-black/60 p-2 opacity-0 transition-opacity group-hover:opacity-100"
                        title="Pobierz PNG"
                      >
                        <Download className="h-4 w-4 text-white" />
                      </button>
                    </div>
                    {/* Label */}
                    <div className="p-3">
                      <p className="text-sm font-medium text-white">{meta.label}</p>
                      <p className="text-xs text-gray-500">{meta.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!result && !isLoading && !error && (
          <div className="rounded-lg border border-dashed border-gray-800 p-6 text-center">
            <ImageIcon className="mx-auto h-8 w-8 text-gray-700" />
            <p className="mt-2 text-sm text-gray-500">
              Najpierw wygeneruj listing powyzej, potem kliknij &quot;Generuj grafiki&quot; aby stworzyc infografiki A+ Content.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
