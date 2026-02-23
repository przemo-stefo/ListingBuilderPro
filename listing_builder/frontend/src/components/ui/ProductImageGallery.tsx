// frontend/src/components/ui/ProductImageGallery.tsx
// Purpose: Product image gallery with primary view + thumbnail strip
// NOT for: Image upload or editing

'use client'

import { useState } from 'react'
import { ImageIcon } from 'lucide-react'

interface ProductImageGalleryProps {
  images: string[]
}

export default function ProductImageGallery({ images }: ProductImageGalleryProps) {
  const [activeIndex, setActiveIndex] = useState(0)

  if (!images.length) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg bg-gray-800">
        <ImageIcon className="h-10 w-10 text-gray-600" />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Primary image */}
      <div className="flex items-center justify-center rounded-lg bg-gray-900 overflow-hidden"
           style={{ maxHeight: '320px' }}>
        <img
          src={images[activeIndex]}
          alt=""
          loading="lazy"
          className="max-h-80 w-auto object-contain"
        />
      </div>

      {/* Thumbnail strip — only show if more than 1 image */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((url, i) => (
            <button
              key={i}
              onClick={() => setActiveIndex(i)}
              className={`h-14 w-14 shrink-0 rounded-lg overflow-hidden border-2 transition-colors ${
                i === activeIndex ? 'border-white' : 'border-transparent hover:border-gray-600'
              }`}
            >
              <img
                src={url}
                alt=""
                loading="lazy"
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
