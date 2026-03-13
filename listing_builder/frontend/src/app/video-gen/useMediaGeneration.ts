// frontend/src/app/video-gen/useMediaGeneration.ts
// Purpose: Generation logic for video (ComfyUI) and images (LLM+Pillow)
// NOT for: UI rendering or state unrelated to generation

import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api/client'
import { createClient } from '@/lib/supabase'
import type { GenerationStatus, InputMode, ImageResult } from './types'

interface UseMediaGenerationProps {
  // WHY: useToast returns a function with broader signature — accept any function
  toast: (opts: Record<string, unknown>) => unknown
}

interface VideoInput {
  inputMode: InputMode
  productUrl: string
  selectedImage: File | null
  prompt: string
}

interface ImageInput {
  productName: string
  brand: string
  bulletPoints: string
  imageTheme: string
}

export function useMediaGeneration({ toast }: UseMediaGenerationProps) {
  const [status, setStatus] = useState<GenerationStatus>('idle')
  const [videoBase64, setVideoBase64] = useState<string | null>(null)
  const [imageResult, setImageResult] = useState<ImageResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reset = useCallback(() => {
    setVideoBase64(null)
    setImageResult(null)
    setStatus('idle')
    setError(null)
  }, [])

  // WHY: Video uses raw fetch() — ComfyUI pipeline takes 2-10 min, apiClient 30s timeout too short
  const generateVideo = useCallback(async ({ inputMode, productUrl, selectedImage, prompt }: VideoInput) => {
    setStatus('generating')
    setError(null)
    setVideoBase64(null)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const authHeader = session?.access_token ? `Bearer ${session.access_token}` : ''
      let resp: Response

      if (inputMode === 'url') {
        resp = await fetch('/api/proxy/video/generate-from-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(authHeader && { 'Authorization': authHeader }) },
          body: JSON.stringify({ url: productUrl.trim(), prompt }),
        })
      } else {
        const formData = new FormData()
        formData.append('image', selectedImage!)
        formData.append('prompt', prompt)
        resp = await fetch('/api/proxy/video/generate', {
          method: 'POST',
          body: formData,
          ...(authHeader && { headers: { 'Authorization': authHeader } }),
        })
      }

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: 'Blad serwera' }))
        throw new Error(data.detail || `HTTP ${resp.status}`)
      }

      const data = await resp.json()
      if (data.status === 'completed' && data.video_base64) {
        setVideoBase64(data.video_base64)
        setStatus('completed')
        toast({ title: 'Wideo gotowe!', description: 'AI wygenerowalo wideo produktowe.' })
      } else if (data.status === 'error') {
        throw new Error(data.error || 'Generowanie nie powiodlo sie')
      } else {
        throw new Error('Nieoczekiwany status odpowiedzi')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Nieznany blad'
      setError(msg)
      setStatus('error')
      toast({ title: 'Blad generowania', description: msg, variant: 'destructive' })
    }
  }, [toast])

  // WHY: Images use apiClient (auto JWT, 120s enough for LLM+Pillow pipeline)
  const generateImages = useCallback(async ({ productName, brand, bulletPoints, imageTheme }: ImageInput) => {
    setStatus('generating')
    setError(null)
    setImageResult(null)

    try {
      const bullets = bulletPoints.split('\n').filter(b => b.trim())
      const { data } = await apiClient.post<ImageResult>('/images/generate', {
        product_name: productName.trim(),
        brand: brand.trim(),
        bullet_points: bullets.length ? bullets : ['Produkt premium'],
        description: '',
        theme: imageTheme,
        llm_provider: 'beast',
      }, { timeout: 120000 })
      setImageResult(data)
      setStatus('completed')
      toast({ title: 'Grafiki gotowe!', description: `Wygenerowano ${data.image_types.length} infografik A+.` })
    } catch (err) {
      const msg = err instanceof Error ? err.message : (err as { message?: string })?.message || 'Nieznany blad'
      setError(msg)
      setStatus('error')
      toast({ title: 'Blad generowania', description: msg, variant: 'destructive' })
    }
  }, [toast])

  return { status, videoBase64, imageResult, error, reset, generateVideo, generateImages, setStatus, setImageResult }
}
