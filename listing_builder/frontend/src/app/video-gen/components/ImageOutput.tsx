// frontend/src/app/video-gen/components/ImageOutput.tsx
// Purpose: Display generated A+ Content infographic images in grid layout
// NOT for: Image generation logic (page.tsx), video output (VideoOutput.tsx)

import { ImageIcon, Download, Loader2 } from 'lucide-react'
import type { GenerationStatus, ImageResult } from '../types'

const IMAGE_TYPE_LABELS: Record<string, { label: string; desc: string }> = {
  hero_banner: { label: 'Baner glowny', desc: 'Naglowek A+ Content z haslem reklamowym' },
  feature_grid: { label: 'Siatka cech', desc: '6 kluczowych cech produktu' },
  comparison: { label: 'Tabela porownawcza', desc: 'Twoj produkt vs konkurencja' },
  specs: { label: 'Specyfikacja', desc: 'Parametry techniczne' },
}

interface Props {
  status: GenerationStatus
  result: ImageResult | null
  error: string | null
  brand?: string
  onRetry: () => void
}

function handleDownload(imageType: string, base64Data: string, brand: string) {
  const link = document.createElement('a')
  link.href = `data:image/png;base64,${base64Data}`
  link.download = `${brand || 'product'}-${imageType}.png`
  link.click()
}

export function ImageOutput({ status, result, error, brand = 'product', onRetry }: Props) {
  const isWorking = status === 'uploading' || status === 'generating'

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 min-h-[400px] flex flex-col">
      <h2 className="mb-4 text-lg font-semibold text-white">Wynik — Grafiki A+</h2>

      {status === 'idle' && !result && (
        <div className="flex-1 flex items-center justify-center text-gray-600">
          <div className="text-center">
            <ImageIcon className="mx-auto h-16 w-16 mb-4 opacity-30" />
            <p>Podaj dane produktu i kliknij &quot;Generuj grafiki&quot;</p>
          </div>
        </div>
      )}

      {isWorking && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-blue-500 mb-4" />
            <p className="text-gray-400 text-lg">AI generuje infografiki...</p>
            <p className="text-gray-600 text-sm mt-2">To moze potrwac 15-30 sekund</p>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <button onClick={onRetry} className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-white hover:bg-gray-700">
              Sprobuj ponownie
            </button>
          </div>
        </div>
      )}

      {status === 'completed' && result && (
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{result.image_types.length} grafik wygenerowanych</span>
            <button
              onClick={() => {
                for (const type of result.image_types) {
                  if (result.images[type]) {
                    setTimeout(() => handleDownload(type, result.images[type], brand), 200)
                  }
                }
              }}
              className="flex items-center gap-1 rounded bg-gray-800 px-2 py-1 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
            >
              <Download className="h-3 w-3" /> Pobierz wszystkie
            </button>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {result.image_types.map((type) => {
              const meta = IMAGE_TYPE_LABELS[type] || { label: type, desc: '' }
              const base64 = result.images[type]
              if (!base64) return null

              return (
                <div key={type} className="group rounded-lg border border-gray-800 bg-[#121212] overflow-hidden">
                  <div className="relative bg-[#0D1117]">
                    <img src={`data:image/png;base64,${base64}`} alt={meta.label} className="w-full h-auto" />
                    <button
                      onClick={() => handleDownload(type, base64, brand)}
                      className="absolute right-2 top-2 rounded-lg bg-black/60 p-2 opacity-0 transition-opacity group-hover:opacity-100"
                    >
                      <Download className="h-4 w-4 text-white" />
                    </button>
                  </div>
                  <div className="p-2">
                    <p className="text-xs font-medium text-white">{meta.label}</p>
                    <p className="text-[10px] text-gray-500">{meta.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
