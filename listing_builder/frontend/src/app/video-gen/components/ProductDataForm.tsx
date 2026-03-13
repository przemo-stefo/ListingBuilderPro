// frontend/src/app/video-gen/components/ProductDataForm.tsx
// Purpose: Product name, brand, bullet points inputs for image generation mode
// NOT for: Video generation inputs (VideoInputControls.tsx) or output display

import { ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const THEMES = [
  { id: 'dark_premium', label: 'Premium (ciemny)' },
  { id: 'light_clean', label: 'Jasny' },
  { id: 'amazon_white', label: 'Amazon (bialy)' },
] as const

interface Props {
  productName: string
  onProductNameChange: (v: string) => void
  brand: string
  onBrandChange: (v: string) => void
  bulletPoints: string
  onBulletPointsChange: (v: string) => void
  imageTheme: string
  onThemeChange: (v: string) => void
}

export function ProductDataForm({
  productName, onProductNameChange,
  brand, onBrandChange,
  bulletPoints, onBulletPointsChange,
  imageTheme, onThemeChange,
}: Props) {
  return (
    <>
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-gray-400" />
          Dane produktu
        </h2>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Nazwa produktu *</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => onProductNameChange(e.target.value)}
            placeholder="np. Nike Air Max 90 Premium"
            className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Marka *</label>
          <input
            type="text"
            value={brand}
            onChange={(e) => onBrandChange(e.target.value)}
            placeholder="np. Nike"
            className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Cechy produktu (opcjonalne, po jednej na linie)</label>
          <textarea
            value={bulletPoints}
            onChange={(e) => onBulletPointsChange(e.target.value)}
            rows={3}
            placeholder={"Technologia Air Max dla maksymalnego komfortu\nSkorzana cholewka premium\nKlasyczny design retro z 1990 roku"}
            className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Styl grafik</h2>
        <div className="flex flex-wrap gap-2">
          {THEMES.map((t) => (
            <button
              key={t.id}
              onClick={() => onThemeChange(t.id)}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm transition-colors',
                imageTheme === t.id ? 'bg-white/10 text-white border border-gray-600' : 'text-gray-500 hover:text-gray-300 border border-gray-800'
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
    </>
  )
}
