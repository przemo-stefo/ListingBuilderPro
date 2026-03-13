// frontend/src/app/video-gen/page.tsx
// Purpose: AI Media Generator — video (ComfyUI) + A+ images (LLM->Pillow)
// NOT for: Generation logic (useMediaGeneration.ts), UI components (components/)

'use client'

import { useState, useRef, useCallback } from 'react'
import { Video, ImageIcon, Sparkles, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useQueryClient } from '@tanstack/react-query'
import { PremiumGate } from '@/components/tier/PremiumGate'
import { useToast } from '@/lib/hooks/useToast'
import { useMediaGen } from '@/components/providers/MediaGenProvider'
import { startGeneration } from '@/lib/api/mediaGeneration'
import { MarketplaceSelector } from './components/MarketplaceSelector'
import { VideoOutput } from './components/VideoOutput'
import { ImageOutput } from './components/ImageOutput'
import { ProductDataForm } from './components/ProductDataForm'
import { InputModeTabs, FileUploadSection, PromptSection, GenerateButton } from './components/VideoInputControls'
import { HowItWorks, InfoCards, UseCases, VideoFaq } from './components/VideoInfoSections'
import { MediaHistoryTab } from './components/MediaHistoryTab'
import { useMediaGeneration } from './useMediaGeneration'
import type { InputMode, MediaMode, ImageResult } from './types'

type PageTab = 'generate' | 'history'

export default function VideoGenPage() {
  const [pageTab, setPageTab] = useState<PageTab>('generate')
  const [mediaMode, setMediaMode] = useState<MediaMode>('video')
  const [inputMode, setInputMode] = useState<InputMode>('url')
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [productUrl, setProductUrl] = useState('')
  const [selectedMarketplace, setSelectedMarketplace] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('product showcase, smooth rotation, studio lighting, white background, commercial quality')
  const [productName, setProductName] = useState('')
  const [brand, setBrand] = useState('')
  const [bulletPoints, setBulletPoints] = useState('')
  const [imageTheme, setImageTheme] = useState('dark_premium')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const { addJob, activeJobs } = useMediaGen()
  const { status, videoBase64, imageResult, error, reset, generateVideo, generateImages, setStatus, setImageResult } = useMediaGeneration({ toast })

  const handleImageSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast({ title: 'Nieprawidlowy plik', description: 'Wybierz obraz (PNG, JPG)', variant: 'destructive' })
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast({ title: 'Plik za duzy', description: 'Maksymalny rozmiar: 10 MB', variant: 'destructive' })
      return
    }
    setSelectedImage(file)
    reset()
    const reader = new FileReader()
    reader.onload = (ev) => setImagePreview(ev.target?.result as string)
    reader.readAsDataURL(file)
  }, [toast, reset])

  const canGenerateVideo = (inputMode === 'file' && !!selectedImage) || (inputMode === 'url' && !!productUrl.trim())
  const canGenerateImages = productName.trim().length >= 3 && brand.trim().length >= 1
  const canGenerate = mediaMode === 'video' ? canGenerateVideo : canGenerateImages
  const isWorking = status === 'uploading' || status === 'generating'

  // WHY: Background generation — starts job on server, user can navigate away
  const handleGenerate = useCallback(async () => {
    if (!canGenerate) return

    if (mediaMode === 'images') {
      try {
        const bullets = bulletPoints.split('\n').filter(b => b.trim())
        const result = await startGeneration({
          media_type: 'images',
          product_name: productName.trim(),
          brand: brand.trim(),
          bullet_points: bullets.length ? bullets : ['Produkt premium'],
          theme: imageTheme,
          llm_provider: 'beast',
        })
        addJob(result.id, 'images')
        // WHY: Invalidate history cache so new job appears immediately in Historia tab
        queryClient.invalidateQueries({ queryKey: ['media-history'] })
        // WHY: Auto-switch to Historia so user sees their job "W kolejce" / "Generuje..."
        setPageTab('history')
        toast({
          title: 'Generowanie rozpoczete',
          description: 'Mozesz swobodnie uzywac panelu. Powiadomimy Cie gdy grafiki beda gotowe.',
        })
      } catch (err) {
        toast({
          title: 'Blad uruchamiania generacji',
          description: (err as Error).message,
          variant: 'destructive',
        })
      }
    } else {
      // WHY: Video still uses direct generation (ComfyUI needs image upload, not easily backgroundable via JSON)
      await generateVideo({ inputMode, productUrl, selectedImage, prompt })
    }
  }, [canGenerate, mediaMode, inputMode, productUrl, selectedImage, prompt, productName, brand, bulletPoints, imageTheme, generateVideo, addJob, toast, queryClient])

  const handleDownload = useCallback(() => {
    if (!videoBase64) return
    const link = document.createElement('a')
    link.href = `data:image/webp;base64,${videoBase64}`
    link.download = `product-video-${Date.now()}.webp`
    link.click()
  }, [videoBase64])

  const handleReset = useCallback(() => {
    setSelectedImage(null)
    setImagePreview(null)
    reset()
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [reset])

  // WHY: When viewing history result, load it into the output panel
  const handleViewHistoryResult = useCallback((result: ImageResult, resultBrand: string) => {
    setImageResult(result)
    setStatus('completed')
    setBrand(resultBrand)
    setMediaMode('images')
    setPageTab('generate')
  }, [setImageResult, setStatus])

  return (
    <PremiumGate feature="Kreator mediow AI">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Sparkles className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Kreator mediow AI</h1>
            <p className="text-sm text-gray-400">Generuj wideo produktowe lub infografiki A+ Content</p>
          </div>
        </div>

        {/* WHY: Page-level tabs — Generuj / Historia */}
        <div className="flex rounded-lg bg-[#121212] p-1 border border-gray-800 max-w-xs">
          <button
            onClick={() => setPageTab('generate')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all',
              pageTab === 'generate' ? 'bg-[#1A1A1A] text-white shadow-sm border border-gray-700' : 'text-gray-500 hover:text-gray-300'
            )}
          >
            <Sparkles className="h-4 w-4" /> Generuj
          </button>
          <button
            onClick={() => setPageTab('history')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all',
              pageTab === 'history' ? 'bg-[#1A1A1A] text-white shadow-sm border border-gray-700' : 'text-gray-500 hover:text-gray-300'
            )}
          >
            <Clock className="h-4 w-4" /> Historia
            {activeJobs.length > 0 && (
              <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
            )}
          </button>
        </div>

        {pageTab === 'history' ? (
          <MediaHistoryTab onViewResult={handleViewHistoryResult} />
        ) : (
          <>
            {/* Media mode toggle */}
            <div className="flex rounded-lg bg-[#121212] p-1 border border-gray-800 max-w-md">
              {([['video', Video, 'Wideo AI'], ['images', ImageIcon, 'Obrazy A+']] as const).map(([mode, Icon, label]) => (
                <button
                  key={mode}
                  onClick={() => { setMediaMode(mode as MediaMode); handleReset() }}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all',
                    mediaMode === mode ? 'bg-[#1A1A1A] text-white shadow-sm border border-gray-700' : 'text-gray-500 hover:text-gray-300'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </button>
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="space-y-4">
                {mediaMode === 'video' ? (
                  <>
                    <InputModeTabs inputMode={inputMode} onChange={setInputMode} />
                    {inputMode === 'url' && (
                      <MarketplaceSelector
                        selectedMarketplace={selectedMarketplace}
                        onSelectMarketplace={(id) => { setSelectedMarketplace(id); setProductUrl('') }}
                        productUrl={productUrl}
                        onUrlChange={setProductUrl}
                      />
                    )}
                    {inputMode === 'file' && (
                      <FileUploadSection imagePreview={imagePreview} fileInputRef={fileInputRef} onImageSelect={handleImageSelect} />
                    )}
                    <PromptSection prompt={prompt} onPromptChange={setPrompt} />
                    <GenerateButton canGenerate={canGenerate} isWorking={isWorking} status={status} onClick={handleGenerate} mediaMode="video" />
                  </>
                ) : (
                  <>
                    <ProductDataForm
                      productName={productName} onProductNameChange={setProductName}
                      brand={brand} onBrandChange={setBrand}
                      bulletPoints={bulletPoints} onBulletPointsChange={setBulletPoints}
                      imageTheme={imageTheme} onThemeChange={setImageTheme}
                    />
                    <GenerateButton canGenerate={canGenerate} isWorking={isWorking} status={status} onClick={handleGenerate} mediaMode="images" />
                  </>
                )}
              </div>

              {mediaMode === 'video' ? (
                <VideoOutput status={status} videoBase64={videoBase64} error={error} onDownload={handleDownload} onReset={handleReset} onRetry={() => setStatus('idle')} />
              ) : (
                <ImageOutput status={status} result={imageResult} error={error} brand={brand} onRetry={() => setStatus('idle')} />
              )}
            </div>

            {mediaMode === 'video' && (
              <>
                <HowItWorks />
                <InfoCards />
                <UseCases />
                <VideoFaq />
              </>
            )}
          </>
        )}
      </div>
    </PremiumGate>
  )
}
