// frontend/src/app/video-gen/page.tsx
// Purpose: Dual-mode video generator — Creatify AI (pro) + template (basic MoviePy)
// NOT for: A+ Content images (removed), ComfyUI (replaced)

'use client'

import { useState, useEffect, useCallback } from 'react'
import { Video, Sparkles, Play, Download, RotateCcw, Loader2, Film, Tag, Zap, Crown, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PremiumGate } from '@/components/tier/PremiumGate'
import apiClient from '@/lib/api/client'

type GenerationMode = 'ai_creatify' | 'template'
type Template = 'product_highlight' | 'feature_breakdown' | 'sale_promo'
type Theme = 'dark_premium' | 'light' | 'amazon_white'
type VisualStyle = 'modern' | 'minimalist' | 'bold' | 'elegant' | 'playful'
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

const VISUAL_STYLES: { id: VisualStyle; name: string }[] = [
  { id: 'modern', name: 'Nowoczesny' },
  { id: 'minimalist', name: 'Minimalistyczny' },
  { id: 'bold', name: 'Odwazny' },
  { id: 'elegant', name: 'Elegancki' },
  { id: 'playful', name: 'Zabawny' },
]

export default function VideoGenPage() {
  const [mode, setMode] = useState<GenerationMode>('ai_creatify')

  // WHY: Creatify mode fields
  const [productUrl, setProductUrl] = useState('')
  const [visualStyle, setVisualStyle] = useState<VisualStyle>('modern')
  const [script, setScript] = useState('')
  const [description, setDescription] = useState('')

  // WHY: Template mode fields
  const [template, setTemplate] = useState<Template>('product_highlight')
  const [theme, setTheme] = useState<Theme>('dark_premium')
  const [originalPrice, setOriginalPrice] = useState('')
  const [salePrice, setSalePrice] = useState('')

  // WHY: Shared fields
  const [productName, setProductName] = useState('')
  const [brand, setBrand] = useState('')
  const [features, setFeatures] = useState('')
  const [imageUrl, setImageUrl] = useState('')

  // WHY: Job state
  const [status, setStatus] = useState<Status>('idle')
  const [jobId, setJobId] = useState<number | null>(null)
  const [videoBase64, setVideoBase64] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const isWorking = status === 'pending' || status === 'running'

  // WHY: Creatify allows just product URL OR product data; template requires name+brand
  const canGenerate = mode === 'ai_creatify'
    ? (productUrl.trim().length > 5 || (productName.trim().length >= 3 && brand.trim().length >= 1))
    : (productName.trim().length >= 3 && brand.trim().length >= 1)

  // WHY: Poll job status — 3s for Creatify (longer jobs), 2s for template
  useEffect(() => {
    if (!jobId || !isWorking) return
    const pollInterval = mode === 'ai_creatify' ? 3000 : 2000
    const interval = setInterval(async () => {
      try {
        const { data } = await apiClient.get(`/media-gen/status/${jobId}`)
        if (data.status === 'completed') {
          setStatus('completed')
          const result = await apiClient.get(`/media-gen/result/${jobId}`)
          const rd = result.data.result_data || {}
          setVideoUrl(rd.video_url || null)
          setVideoBase64(rd.video_base64 || null)
        } else if (data.status === 'failed') {
          setStatus('failed')
          setError(data.error_message || 'Generacja nie powiodla sie')
        }
      } catch {
        // WHY: Network hiccup — keep polling, don't fail
      }
    }, pollInterval)
    return () => clearInterval(interval)
  }, [jobId, isWorking, mode])

  const handleGenerate = useCallback(async () => {
    if (!canGenerate) return
    setStatus('pending')
    setError(null)
    setVideoBase64(null)
    setVideoUrl(null)

    try {
      const featureList = features.split('\n').filter(f => f.trim())

      const payload: Record<string, unknown> = {
        media_type: 'video',
        generation_mode: mode,
        product_name: productName.trim() || undefined,
        brand: brand.trim() || undefined,
        image_url: imageUrl.trim() || undefined,
      }

      if (mode === 'ai_creatify') {
        payload.product_url = productUrl.trim() || undefined
        payload.visual_style = visualStyle
        payload.script = script.trim() || undefined
        payload.description = description.trim() || undefined
        if (featureList.length) payload.features = featureList
      } else {
        payload.template = template
        payload.theme = theme
        payload.features = featureList.length ? featureList : ['Produkt premium']
        payload.original_price = originalPrice.trim() || undefined
        payload.sale_price = salePrice.trim() || undefined
      }

      const { data } = await apiClient.post('/media-gen/start', payload)
      setJobId(data.id)
      setStatus('pending')
    } catch (err: unknown) {
      setStatus('failed')
      const e = err as { response?: { data?: { detail?: string } }; message?: string }
      setError(e.response?.data?.detail || e.message || 'Blad uruchamiania generacji')
    }
  }, [canGenerate, mode, productName, brand, features, imageUrl, productUrl, visualStyle, script, description, template, theme, originalPrice, salePrice])

  const handleDownload = useCallback(() => {
    if (videoUrl) {
      window.open(videoUrl, '_blank')
    } else if (videoBase64) {
      const link = document.createElement('a')
      link.href = `data:video/mp4;base64,${videoBase64}`
      link.download = `tiktok-${template}-${Date.now()}.mp4`
      link.click()
    }
  }, [videoUrl, videoBase64, template])

  const handleReset = useCallback(() => {
    setStatus('idle')
    setJobId(null)
    setVideoBase64(null)
    setVideoUrl(null)
    setError(null)
  }, [])

  const hasVideo = videoUrl || videoBase64
  const videoSrc = videoUrl || (videoBase64 ? `data:video/mp4;base64,${videoBase64}` : '')

  return (
    <PremiumGate feature="Generator TikTok">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Video className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Generator Wideo</h1>
            <p className="text-sm text-gray-400">Profesjonalne wideo produktowe 9:16</p>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setMode('ai_creatify')}
            className={cn(
              'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all',
              mode === 'ai_creatify'
                ? 'border-blue-500 bg-blue-500/10 text-white'
                : 'border-gray-700 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
            )}
          >
            <Crown className="h-4 w-4" />
            AI Creatify
            <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[10px] font-bold uppercase">PRO</span>
          </button>
          <button
            onClick={() => setMode('template')}
            className={cn(
              'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all',
              mode === 'template'
                ? 'border-blue-500 bg-blue-500/10 text-white'
                : 'border-gray-700 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
            )}
          >
            <Film className="h-4 w-4" />
            Szablon
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Form */}
          <div className="space-y-4">
            {mode === 'ai_creatify' ? (
              <>
                {/* Creatify: URL input */}
                <div className="space-y-3 rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
                  <div>
                    <label className="mb-1 block text-sm text-gray-400">URL produktu (Creatify przeskanuje strone)</label>
                    <input
                      type="text"
                      value={productUrl}
                      onChange={e => setProductUrl(e.target.value)}
                      placeholder="https://amazon.de/dp/B0..."
                      className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                    <p className="mt-1 text-xs text-gray-600">Lub wypelnij dane produktu ponizej</p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-400">Nazwa produktu</label>
                      <input
                        type="text"
                        value={productName}
                        onChange={e => setProductName(e.target.value)}
                        placeholder="np. Sluchawki ProMax"
                        className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-400">Marka</label>
                      <input
                        type="text"
                        value={brand}
                        onChange={e => setBrand(e.target.value)}
                        placeholder="np. TechBrand"
                        className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm text-gray-400">Opis produktu</label>
                    <textarea
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                      placeholder="Krotki opis produktu..."
                      rows={2}
                      className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm text-gray-400">URL zdjecia produktu</label>
                    <input
                      type="text"
                      value={imageUrl}
                      onChange={e => setImageUrl(e.target.value)}
                      placeholder="https://..."
                      className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Visual style */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-300">Styl wizualny</label>
                  <div className="flex flex-wrap gap-2">
                    {VISUAL_STYLES.map(s => (
                      <button
                        key={s.id}
                        onClick={() => setVisualStyle(s.id)}
                        className={cn(
                          'rounded-lg border px-3 py-1.5 text-sm transition-all',
                          visualStyle === s.id
                            ? 'border-blue-500 bg-blue-500/10 text-white'
                            : 'border-gray-700 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
                        )}
                      >
                        {s.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Script */}
                <div>
                  <label className="mb-1 block text-sm text-gray-400">Skrypt lektora (opcjonalnie)</label>
                  <textarea
                    value={script}
                    onChange={e => setScript(e.target.value)}
                    placeholder="Creatify wygeneruje skrypt automatycznie jesli puste..."
                    rows={3}
                    className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </>
            ) : (
              <>
                {/* Template mode — original form */}
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
              </>
            )}

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
                  {status === 'pending' ? 'W kolejce...' : mode === 'ai_creatify' ? 'Creatify generuje...' : 'Renderowanie wideo...'}
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  {mode === 'ai_creatify' ? 'Generuj wideo AI' : 'Generuj wideo z szablonu'}
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
                <p className="mt-1 text-xs text-gray-600">
                  {mode === 'ai_creatify' ? 'Profesjonalne wideo AI z awatarem i lektorem' : 'Wideo 9:16 (1080x1920) • MP4 • ~20s'}
                </p>
              </div>
            )}

            {isWorking && (
              <div className="flex h-full min-h-[400px] flex-col items-center justify-center">
                <Loader2 className="mb-3 h-12 w-12 animate-spin text-blue-400" />
                <p className="text-sm text-gray-300">
                  {status === 'pending' ? 'Zadanie w kolejce...' : mode === 'ai_creatify' ? 'Creatify renderuje wideo...' : 'Renderowanie wideo...'}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {mode === 'ai_creatify' ? 'To moze potrwac 2-5 minut' : 'To moze potrwac 30-60 sekund'}
                </p>
              </div>
            )}

            {status === 'completed' && hasVideo && (
              <div className="space-y-4">
                <video
                  src={videoSrc}
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
                    {videoUrl ? <ExternalLink className="h-4 w-4" /> : <Download className="h-4 w-4" />}
                    {videoUrl ? 'Otworz wideo' : 'Pobierz MP4'}
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
