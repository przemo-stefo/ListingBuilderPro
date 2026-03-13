// frontend/src/app/video-gen/components/VideoInputControls.tsx
// Purpose: Input mode tabs, file upload, prompt editor, generate button
// NOT for: Marketplace URL selection (MarketplaceSelector.tsx) or output display

import { Upload, Link2, Sparkles, Video, Loader2, Image as ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { InputMode, GenerationStatus, MediaMode } from '../types'

const PROMPT_PRESETS = [
  'product showcase, rotation, studio lighting',
  'zoom in, dramatic lighting, dark background',
  'floating product, particles, cinematic',
  'unboxing effect, revealing product, clean',
]

export function InputModeTabs({ inputMode, onChange }: { inputMode: InputMode; onChange: (m: InputMode) => void }) {
  return (
    <div className="flex rounded-lg bg-[#121212] p-1 border border-gray-800">
      {([['url', Link2, 'Link do produktu'], ['file', Upload, 'Wgraj zdjecie']] as const).map(([mode, Icon, label]) => (
        <button
          key={mode}
          onClick={() => onChange(mode as InputMode)}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all',
            inputMode === mode ? 'bg-[#1A1A1A] text-white shadow-sm border border-gray-700' : 'text-gray-500 hover:text-gray-300'
          )}
        >
          <Icon className="h-4 w-4" />
          {label}
        </button>
      ))}
    </div>
  )
}

export function FileUploadSection({ imagePreview, fileInputRef, onImageSelect }: {
  imagePreview: string | null
  fileInputRef: React.RefObject<HTMLInputElement | null>
  onImageSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
      <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
        <ImageIcon className="h-5 w-5 text-gray-400" />
        Zdjecie produktu
      </h2>
      <input ref={fileInputRef as React.RefObject<HTMLInputElement>} type="file" accept="image/png,image/jpeg,image/webp" onChange={onImageSelect} className="hidden" />
      {imagePreview ? (
        <div className="relative group">
          <img src={imagePreview} alt="Podglad produktu" className="w-full max-h-80 object-contain rounded-lg border border-gray-700" />
          <button onClick={() => fileInputRef.current?.click()} className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg">
            <span className="text-sm text-white bg-gray-800 px-3 py-1.5 rounded-lg">Zmien zdjecie</span>
          </button>
        </div>
      ) : (
        <button onClick={() => fileInputRef.current?.click()} className="w-full rounded-lg border-2 border-dashed border-gray-700 p-12 text-center hover:border-gray-500 transition-colors">
          <Upload className="mx-auto h-10 w-10 text-gray-500 mb-3" />
          <p className="text-gray-400">Kliknij aby wybrac zdjecie</p>
          <p className="text-xs text-gray-600 mt-1">PNG, JPG lub WebP (max 10 MB)</p>
        </button>
      )}
    </div>
  )
}

export function PromptSection({ prompt, onPromptChange }: { prompt: string; onPromptChange: (v: string) => void }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
      <h2 className="mb-3 text-lg font-semibold text-white flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-gray-400" />
        Opis ruchu
      </h2>
      <textarea value={prompt} onChange={(e) => onPromptChange(e.target.value)} rows={3}
        className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        placeholder="np. product showcase, smooth rotation, studio lighting..."
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {PROMPT_PRESETS.map((preset) => (
          <button key={preset} onClick={() => onPromptChange(preset)}
            className="rounded-md bg-gray-800 px-2.5 py-1 text-xs text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
          >{preset.split(',')[0]}</button>
        ))}
      </div>
    </div>
  )
}

export function GenerateButton({ canGenerate, isWorking, status, onClick, mediaMode = 'video' }: {
  canGenerate: boolean; isWorking: boolean; status: GenerationStatus; onClick: () => void; mediaMode?: 'video' | 'images'
}) {
  const isImages = mediaMode === 'images'
  return (
    <button onClick={onClick} disabled={!canGenerate || isWorking}
      className={cn(
        'w-full rounded-xl py-4 text-lg font-semibold transition-all flex items-center justify-center gap-3',
        canGenerate && !isWorking
          ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white hover:from-blue-500 hover:to-cyan-400 shadow-lg shadow-blue-500/20'
          : 'bg-gray-800 text-gray-500 cursor-not-allowed'
      )}
    >
      {isWorking ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin" />
          {isImages ? 'Generowanie grafik (15-30s)...' : status === 'uploading' ? 'Wysylanie...' : 'Generowanie wideo (2-5 min)...'}
        </>
      ) : (
        <>{isImages ? <ImageIcon className="h-5 w-5" /> : <Video className="h-5 w-5" />} {isImages ? 'Generuj grafiki A+' : 'Generuj wideo AI'}</>
      )}
    </button>
  )
}
