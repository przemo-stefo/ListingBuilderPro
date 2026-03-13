// frontend/src/app/video-gen/components/MarketplaceSelector.tsx
// Purpose: Marketplace grid with flags + URL input for video generation
// NOT for: File upload (that's in page.tsx) or video output display

import { Globe, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

// WHY: Marketplace definitions with flags for URL-based video generation
export const MARKETPLACES = [
  { id: 'amazon_de', label: 'Amazon DE', flag: '\u{1F1E9}\u{1F1EA}', domain: 'amazon.de', placeholder: 'https://www.amazon.de/dp/B0...' },
  { id: 'amazon_com', label: 'Amazon US', flag: '\u{1F1FA}\u{1F1F8}', domain: 'amazon.com', placeholder: 'https://www.amazon.com/dp/B0...' },
  { id: 'amazon_co_uk', label: 'Amazon UK', flag: '\u{1F1EC}\u{1F1E7}', domain: 'amazon.co.uk', placeholder: 'https://www.amazon.co.uk/dp/B0...' },
  { id: 'amazon_pl', label: 'Amazon PL', flag: '\u{1F1F5}\u{1F1F1}', domain: 'amazon.pl', placeholder: 'https://www.amazon.pl/dp/B0...' },
  { id: 'allegro', label: 'Allegro', flag: '\u{1F1F5}\u{1F1F1}', domain: 'allegro.pl', placeholder: 'https://allegro.pl/oferta/...' },
  { id: 'ebay', label: 'eBay', flag: '\u{1F30D}', domain: 'ebay.com', placeholder: 'https://www.ebay.com/itm/...' },
  { id: 'kaufland', label: 'Kaufland', flag: '\u{1F1E9}\u{1F1EA}', domain: 'kaufland.de', placeholder: 'https://www.kaufland.de/product/...' },
  { id: 'rozetka', label: 'Rozetka', flag: '\u{1F1FA}\u{1F1E6}', domain: 'rozetka.com.ua', placeholder: 'https://rozetka.com.ua/...' },
  { id: 'aliexpress', label: 'AliExpress', flag: '\u{1F1E8}\u{1F1F3}', domain: 'aliexpress.com', placeholder: 'https://www.aliexpress.com/item/...' },
  { id: 'temu', label: 'Temu', flag: '\u{1F30D}', domain: 'temu.com', placeholder: 'https://www.temu.com/...' },
] as const

interface Props {
  selectedMarketplace: string | null
  onSelectMarketplace: (id: string) => void
  productUrl: string
  onUrlChange: (url: string) => void
}

export function MarketplaceSelector({ selectedMarketplace, onSelectMarketplace, productUrl, onUrlChange }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
      <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
        <Globe className="h-5 w-5 text-gray-400" />
        Wybierz marketplace
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-5">
        {MARKETPLACES.map((mp) => (
          <button
            key={mp.id}
            onClick={() => onSelectMarketplace(mp.id)}
            className={cn(
              'flex flex-col items-center gap-1 rounded-lg px-3 py-3 text-xs font-medium transition-all border',
              selectedMarketplace === mp.id
                ? 'border-blue-500 bg-blue-500/10 text-white shadow-sm shadow-blue-500/10'
                : 'border-gray-700 bg-[#121212] text-gray-400 hover:border-gray-500 hover:text-gray-200'
            )}
          >
            <span className="text-xl leading-none">{mp.flag}</span>
            <span className="truncate w-full text-center">{mp.label}</span>
          </button>
        ))}
      </div>

      {selectedMarketplace ? (
        <div className="space-y-3">
          <div className="relative">
            <ExternalLink className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="url"
              value={productUrl}
              onChange={(e) => onUrlChange(e.target.value)}
              placeholder={MARKETPLACES.find(m => m.id === selectedMarketplace)?.placeholder || 'Wklej link do produktu...'}
              className="w-full rounded-lg border border-gray-700 bg-[#121212] pl-10 pr-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <p className="text-xs text-gray-600">
            Wklej pelny link do oferty — AI automatycznie pobierze zdjecie produktu i wygeneruje wideo.
          </p>
        </div>
      ) : (
        <p className="text-sm text-gray-500 text-center py-2">
          Wybierz marketplace powyzej, aby wkleic link do produktu
        </p>
      )}
    </div>
  )
}
