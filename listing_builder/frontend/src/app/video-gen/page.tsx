// frontend/src/app/video-gen/page.tsx
// Purpose: TikTok 9:16 Video Generator — template-based product videos
// NOT for: A+ Content images (removed), ComfyUI (replaced with MoviePy)

'use client'

import { useState, useEffect, useCallback } from 'react'
import { Video, Sparkles, Play, Download, RotateCcw, Loader2, Film, Tag, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PremiumGate } from '@/components/tier/PremiumGate'
import apiClient from '@/lib/api/client'

type Template = 'product_highlight' | 'feature_breakdown' | 'sale_promo'
type Theme = 'dark_premium' | 'light' | 'amazon_white'
type Status = 'idle' | 'pending' | 'running' | 'completed' | 'failed'

const TEMPLATES: { id: Template; name: string; icon: typeof Film; desc: string }[] = [
  { id: 'product_highlight', name: 'Prezentacja', icon: Film, desc: 'Hero + produkt + cechy + CTA' },
  { id: 'feature_breakdown', name: 'Cechy', icon: Zap, desc: 'Kazda cecha osobno z numerem' },
  { id: 'sale_promo', name: 'Promocja', icon: Tag, desc: 'Cena, rabat, urgency CTA' },
]

const THEMES: { id: Theme; name: string; colors: string }[] = [
  { id: 'dark_premium', name: 'Ciemny', colors: 'bg-gray-900' },
  { id: 'light', name: 'Jasny', colors: 'bg-gray-200' },
  { id: 'amazon_white', name: 'Amazon', colors: 'bg-orange-100' },
]

export default function VideoGenPage() {
  const [template, setTemplate] = useState<Template>('product_highlight')
  const [theme, setTheme] = useState<Theme>('dark_premium')
  const [productName, setProductName] = useState('')
  const [brand, setBrand] = useState('')
  const [features, setFeatures] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [originalPrice, setOriginalPrice] = useState('')
  const [salePrice, setSalePrice] = useState('')

  const [status, setStatus] = useState<Status>('idle')
  const [jobId, setJobId] = useState<number | null>(null)
  const [videoBase64, setVideoBase64] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const canGenerate = productName.trim().length >= 3 && brand.trim().length >= 1
  const isWorking = status === 'pending' || status === 'running'

  // WHY: Poll job status every 2s until completed/failed
  useEffect(() => {
    if (!jobId || !isWorking) return
    const interval = setInterval(async () => {
      try {
        const { data } = await apiClient.get(`/media-gen/status/${jobId}`)
        if (data.status === 'completed') {
          setStatus('completed')
          const result = await apiClient.get(`/media-gen/result/${jobId}`)
          setVideoBase64(result.data.result_data?.video_base64 || null)
        } else if (data.status === 'failed') {
          setStatus('failed')
          setError(data.error_message || 'Generacja nie powiodla sie')
        }
      } catch {
        // WHY: Network hiccup — keep polling, don't fail
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [jobId, isWorking])

  const handleGenerate = useCallback(async () => {
    if (!canGenerate) return
    setStatus('pending')
    setError(null)
    setVideoBase64(null)

    try {
      const featureList = features.split('\n').filter(f => f.trim())
      const { data } = await apiClient.post('/media-gen/start', {
        media_type: 'video',
        template,
        product_name: productName.trim(),
        brand: brand.trim(),
        features: featureList.length ? featureList : ['Produkt premium'],
        theme,
        image_url: imageUrl.trim() || undefined,
        original_price: originalPrice.trim() || undefined,
        sale_price: salePrice.trim() || undefined,
      })
      setJobId(data.id)
      setStatus('pending')
    } catch (err: any) {
      setStatus('failed')
      setError(err.response?.data?.detail || err.message || 'Blad uruchamiania generacji')
    }
  }, [canGenerate, template, productName, brand, features, theme, imageUrl, originalPrice, salePrice])

  const handleDownload = useCallback(() => {
    if (!videoBase64) return
    const link = document.createElement('a')
    link.href = `data:video/mp4;base64,${videoBase64}`
    link.download = `tiktok-${template}-${Date.now()}.mp4`
    link.click()
  }, [videoBase64, template])

  const handleReset = useCallback(() => {
    setStatus('idle')
    setJobId(null)
    setVideoBase64(null)
    setError(null)
  }, [])

  return (
    <PremiumGate feature="Generator TikTok">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Video className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Generator TikTok / Reels</h1>
            <p className="text-sm text-gray-400">Wideo produktowe 9:16 z szablonami i efektami</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Form */}
          <div className="space-y-4">
            {/* Template picker */}
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">Szablon</label>
              <div className="grid grid-cols-3 gap-2">
                {TEMPLATES.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setTemplate(t.id)}
                    className={cn(
                      'rounded-lg border p-3 text-left transition-all',
                      template === t.id
                        ? 'border-blue-500 bg-blue-500/10 text-white'
                        : 'border-gray-700 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
                    )}
                  >
                    <t.icon className="mb-1 h-5 w-5" />
                    <div className="text-sm font-medium">{t.name}</div>
                    <div className="text-xs text-gray-500">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Theme picker */}
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">Motyw</label>
              <div className="flex gap-2">
                {THEMES.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={cn(
                      'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-all',
                      theme === t.id
                        ? 'border-blue-500 bg-blue-500/10 text-white'
                        : 'border-gray-700 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
                    )}
                  >
                    <div className={cn('h-3 w-3 rounded-full', t.colors)} />
                    {t.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Product data */}
            <div className="space-y-3 rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
              <div>
                <label className="mb-1 block text-sm text-gray-400">Nazwa produktu *</label>
                <input
                  type="text"
                  value={productName}
                  onChange={e => setProductName(e.target.value)}
                  placeholder="np. Bezprzewodowe sluchawki ProMax"
                  className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">Marka *</label>
                <input
                  type="text"
                  value={brand}
                  onChange={e => setBrand(e.target.value)}
                  placeholder="np. TechBrand"
                  className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">Cechy produktu (jedna na linie)</label>
                <textarea
                  value={features}
                  onChange={e => setFeatures(e.target.value)}
                  placeholder={"Redukcja szumow ANC\nBateria 40h\nBluetooth 5.3\nSzybkie ladowanie"}
                  rows={4}
                  className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">URL zdjecia produktu (opcjonalnie)</label>
                <input
                  type="text"
                  value={imageUrl}
                  onChange={e => setImageUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              {/* WHY: Price fields only for sale_promo template */}
              {template === 'sale_promo' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-sm text-gray-400">Cena oryginalna</label>
                    <input
                      type="text"
                      value={originalPrice}
                      onChange={e => setOriginalPrice(e.target.value)}
                      placeholder="199 zl"
                      className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-gray-400">Cena promocyjna</label>
                    <input
                      type="text"
                      value={salePrice}
                      onChange={e => setSalePrice(e.target.value)}
                      placeholder="149 zl"
                      className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={!canGenerate || isWorking}
              className={cn(
                'flex w-full items-center justify-center gap-2 rounded-lg px-6 py-3 text-sm font-medium transition-all',
                canGenerate && !isWorking
                  ? 'bg-blue-600 text-white hover:bg-blue-500'
                  : 'cursor-not-allowed bg-gray-800 text-gray-500'
              )}
            >
              {isWorking ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {status === 'pending' ? 'W kolejce...' : 'Generuje wideo...'}
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generuj wideo TikTok
                </>
              )}
            </button>
          </div>

          {/* Right: Output */}
          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-6">
            {status === 'idle' && (
              <div className="flex h-full min-h-[400px] flex-col items-center justify-center text-gray-500">
                <Play className="mb-3 h-12 w-12" />
                <p className="text-sm">Wypelnij dane i kliknij Generuj</p>
                <p className="mt-1 text-xs text-gray-600">Wideo 9:16 (1080x1920) • MP4 • ~20s</p>
              </div>
            )}

            {isWorking && (
              <div className="flex h-full min-h-[400px] flex-col items-center justify-center">
                <Loader2 className="mb-3 h-12 w-12 animate-spin text-blue-400" />
                <p className="text-sm text-gray-300">
                  {status === 'pending' ? 'Zadanie w kolejce...' : 'Renderowanie wideo...'}
                </p>
                <p className="mt-1 text-xs text-gray-500">To moze potrwac 30-60 sekund</p>
              </div>
            )}

            {status === 'completed' && videoBase64 && (
              <div className="space-y-4">
                <video
                  src={`data:video/mp4;base64,${videoBase64}`}
                  controls
                  autoPlay
                  loop
                  muted
                  className="mx-auto max-h-[500px] rounded-lg"
                  style={{ aspectRatio: '9/16' }}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleDownload}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500"
                  >
                    <Download className="h-4 w-4" />
                    Pobierz MP4
                  </button>
                  <button
                    onClick={handleReset}
                    className="flex items-center justify-center gap-2 rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-400 hover:text-white"
                  >
                    <RotateCcw className="h-4 w-4" />
                    Nowe
                  </button>
                </div>
              </div>
            )}

            {status === 'failed' && (
              <div className="flex h-full min-h-[400px] flex-col items-center justify-center">
                <div className="mb-3 rounded-lg bg-red-500/10 p-4 text-center">
                  <p className="text-sm text-red-400">{error || 'Wystapil blad'}</p>
                </div>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-400 hover:text-white"
                >
                  <RotateCcw className="h-4 w-4" />
                  Sprobuj ponownie
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </PremiumGate>
  )
}
