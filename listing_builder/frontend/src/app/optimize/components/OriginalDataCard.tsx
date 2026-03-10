// frontend/src/app/optimize/components/OriginalDataCard.tsx
// Purpose: Read-only display of imported product data (images, bullets, description)
// NOT for: Editing product data or optimization results

import { Database } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import ProductImageGallery from '@/components/ui/ProductImageGallery'

interface OriginalDataCardProps {
  images: string[]
  bullets: string[]
  description: string
}

export function OriginalDataCard({ images, bullets, description }: OriginalDataCardProps) {
  if (images.length === 0 && bullets.length === 0 && !description) return null

  return (
    <Card className="border-gray-800 bg-[#121212]">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-gray-500" />
          <span className="text-xs font-medium text-gray-400">Oryginalne dane z importu</span>
          <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-500">z bazy</span>
        </div>
        {images.length > 0 && (
          <ProductImageGallery images={images} />
        )}
        {bullets.length > 0 && (
          <div>
            <p className="mb-1 text-[10px] uppercase tracking-wider text-gray-600">Bullet points</p>
            <ul className="space-y-1">
              {bullets.map((b, i) => (
                <li key={i} className="text-xs text-gray-400 leading-relaxed">
                  <span className="text-gray-600 mr-1">{i + 1}.</span>{b}
                </li>
              ))}
            </ul>
          </div>
        )}
        {description && (
          <div>
            <p className="mb-1 text-[10px] uppercase tracking-wider text-gray-600">Opis</p>
            <p className="text-xs text-gray-400 leading-relaxed line-clamp-4">{description}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
