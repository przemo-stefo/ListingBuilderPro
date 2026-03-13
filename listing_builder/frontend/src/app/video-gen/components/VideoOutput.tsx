// frontend/src/app/video-gen/components/VideoOutput.tsx
// Purpose: Video generation output panel — idle, loading, error, completed states
// NOT for: Input handling or marketplace selection

import { Video, Loader2, Download, RefreshCw } from 'lucide-react'

type GenerationStatus = 'idle' | 'uploading' | 'generating' | 'completed' | 'error'

interface Props {
  status: GenerationStatus
  videoBase64: string | null
  error: string | null
  onDownload: () => void
  onReset: () => void
  onRetry: () => void
}

export function VideoOutput({ status, videoBase64, error, onDownload, onReset, onRetry }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 min-h-[400px] flex flex-col">
      <h2 className="mb-4 text-lg font-semibold text-white">Wynik</h2>

      {status === 'idle' && !videoBase64 && (
        <div className="flex-1 flex items-center justify-center text-gray-600">
          <div className="text-center">
            <Video className="mx-auto h-16 w-16 mb-4 opacity-30" />
            <p>Wklej link lub wgraj zdjecie i kliknij &quot;Generuj&quot;</p>
          </div>
        </div>
      )}

      {(status === 'generating' || status === 'uploading') && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-blue-500 mb-4" />
            <p className="text-gray-400 text-lg">AI generuje wideo...</p>
            <p className="text-gray-600 text-sm mt-2">To moze potrwac 2-5 minut</p>
            <div className="mt-4 w-64 mx-auto h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-600 to-cyan-500 rounded-full animate-progress" />
            </div>
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

      {status === 'completed' && videoBase64 && (
        <div className="flex-1 flex flex-col">
          <div className="flex-1 flex items-center justify-center bg-black/30 rounded-lg mb-4">
            <img src={`data:image/webp;base64,${videoBase64}`} alt="Wygenerowane wideo produktowe" className="max-h-[350px] rounded-lg" />
          </div>
          <div className="flex gap-3">
            <button onClick={onDownload} className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-green-600 py-3 text-white hover:bg-green-500 transition-colors">
              <Download className="h-4 w-4" /> Pobierz wideo
            </button>
            <button onClick={onReset} className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-3 text-gray-300 hover:bg-gray-700 transition-colors">
              <RefreshCw className="h-4 w-4" /> Nowe
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
