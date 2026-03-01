// frontend/src/app/products/import/components/SingleImport.tsx
// Purpose: Single product import form (ASIN/URL/manual + URL scraping)
// NOT for: Batch import or optimization

'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { importSingleProduct, scrapeProductUrl } from '@/lib/api/import'
import { useToast } from '@/lib/hooks/useToast'
import { cn } from '@/lib/utils'
import {
  Upload,
  Link2,
  Package,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Loader2,
  Download,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'
import { MARKETPLACES } from '../constants'

// WHY: Detect marketplace from pasted URL to auto-select and enable scraping
function detectMarketplace(url: string): string | null {
  try {
    const hostname = new URL(url).hostname.toLowerCase()
    if (hostname.includes('allegro')) return 'allegro'
    if (hostname.includes('amazon')) return 'amazon'
    if (hostname.includes('ebay')) return 'ebay'
    if (hostname.includes('kaufland')) return 'kaufland'
    if (hostname.includes('rozetka')) return 'rozetka'
    if (hostname.includes('aliexpress')) return 'aliexpress'
    if (hostname.includes('temu')) return 'temu'
  } catch { /* not a valid URL */ }
  return null
}

// WHY: Marketplaces with backend scraping support
const SCRAPEABLE = new Set(['allegro', 'rozetka', 'aliexpress', 'temu'])

// WHY: Show relevant example URL when marketplace is selected
const URL_PLACEHOLDERS: Record<string, string> = {
  amazon: 'https://amazon.de/dp/B0XXXXXXXX',
  allegro: 'https://allegro.pl/oferta/...',
  ebay: 'https://ebay.com/itm/...',
  kaufland: 'https://kaufland.de/product/...',
  rozetka: 'https://rozetka.com.ua/ua/.../p123456/',
  aliexpress: 'https://aliexpress.com/item/1005XXXXXXXXX.html',
  temu: 'https://temu.com/goods-detail-g-XXXXXXXXX.html',
}

// WHY: ASIN format = 10 chars starting with B0 or digit. Outside component to avoid re-creation.
const ASIN_PATTERN = /^[B0-9][A-Z0-9]{9}$/i

// WHY: Extract readable title from URL slug instead of showing raw URL as product title
function titleFromUrl(url: string): string {
  try {
    const path = new URL(url).pathname
    // Allegro: /oferta/kolumna-1000w-glosnik-bezprzewodowy → "kolumna 1000w glosnik bezprzewodowy"
    const slug = path.split('/').filter(Boolean).pop() || ''
    // Remove numeric ID suffix (Allegro appends offer ID at end)
    const clean = slug.replace(/-\d{8,}$/, '').replace(/-/g, ' ').trim()
    return clean || 'Produkt bez nazwy'
  } catch {
    return 'Produkt bez nazwy'
  }
}

export default function SingleImport() {
  const router = useRouter()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [marketplace, setMarketplace] = useState('amazon')
  const [asin, setAsin] = useState('')
  const [productUrl, setProductUrl] = useState('')
  const [showDetails, setShowDetails] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [bullets, setBullets] = useState<string[]>([''])
  const [brand, setBrand] = useState('')
  const [price, setPrice] = useState('')
  const [category, setCategory] = useState('')
  // WHY: Store images from scrape so they get sent with the import request
  const [images, setImages] = useState<string[]>([])
  const [scraped, setScraped] = useState(false)
  const [importSuccess, setImportSuccess] = useState(false)

  // WHY: Auto-detect marketplace when user pastes a URL
  const handleUrlChange = useCallback((url: string) => {
    setProductUrl(url)
    setScraped(false)
    const detected = detectMarketplace(url)
    if (detected) setMarketplace(detected)
  }, [])

  // WHY: Scrape mutation fetches data WITHOUT importing — user reviews first
  const scrapeMutation = useMutation({
    mutationFn: async () => {
      return await scrapeProductUrl(productUrl, marketplace)
    },
    onSuccess: (data) => {
      if (data.title) setTitle(data.title)
      if (data.price) setPrice(String(data.price))
      if (data.brand) setBrand(data.brand)
      if (data.category) setCategory(data.category)
      if (data.description) setDescription(data.description)
      if (data.source_id) setAsin(data.source_id)
      if (data.bullet_points?.length) setBullets(data.bullet_points)
      if (data.images?.length) setImages(data.images)
      setShowDetails(true)
      setScraped(true)
      toast({ title: 'Dane pobrane', description: `${data.title?.slice(0, 60)}...` })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd scrapowania', description: error.message, variant: 'destructive' })
    },
  })

  const importMutation = useMutation({
    mutationFn: async () => {
      const cleanBullets = bullets.filter(b => b.trim())
      const product = {
        source_platform: marketplace,
        source_id: asin || 'manual',
        source_url: productUrl || undefined,
        title: title || asin || (productUrl ? titleFromUrl(productUrl) : 'Produkt bez nazwy'),
        brand: brand || undefined,
        price: price ? parseFloat(price) : undefined,
        category: category || undefined,
        description: description || undefined,
        // WHY: Backend ProductImport expects images as top-level field
        images: images.length > 0 ? images : undefined,
        // WHY: Backend stores bullet_points inside attributes JSONB, not as top-level field
        attributes: cleanBullets.length > 0 ? { bullet_points: cleanBullets } : undefined,
      }
      return await importSingleProduct(product)
    },
    onSuccess: () => {
      toast({ title: 'Produkt zaimportowany', description: 'Produkt został dodany do systemu' })
      // WHY: Invalidate so dashboard stats + product list reflect the new import
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      setImportSuccess(true)
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd importu', description: error.message, variant: 'destructive' })
    },
  })

  // WHY: ASIN format check — warning only, not blocking (user may enter custom IDs)
  const asinWarning = asin.trim() && !ASIN_PATTERN.test(asin.trim())
    ? 'ASIN powinien mieć 10 znaków (np. B0XXXXXXXX)' : ''

  const canSubmit = asin.trim() || productUrl.trim() || title.trim()
  const canScrape = productUrl.trim() && SCRAPEABLE.has(marketplace) && !scrapeMutation.isPending

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) {
      toast({ title: 'Brakujące dane', description: 'Podaj ASIN, link lub tytuł', variant: 'destructive' })
      return
    }
    importMutation.mutate()
  }

  const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

  // WHY: Post-import success view — nudge user to optimize instead of just showing product list
  if (importSuccess) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-8 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-green-500 mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Produkt zaimportowany!</h3>
        <p className="text-sm text-gray-400 mb-6">Co chcesz zrobić dalej?</p>
        <div className="flex justify-center gap-3">
          <Link
            href="/optimize"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            <Sparkles className="h-4 w-4" />
            Optymalizuj teraz
          </Link>
          <Link
            href="/products"
            className="inline-flex items-center gap-2 rounded-lg border border-gray-700 px-5 py-2.5 text-sm font-medium text-gray-300 hover:border-gray-500 transition-colors"
          >
            Zobacz produkty
          </Link>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Marketplace selector */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <label className="text-sm font-medium text-white mb-3 block">Marketplace</label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {MARKETPLACES.map((mp) => (
            <button
              key={mp.value}
              type="button"
              onClick={() => setMarketplace(mp.value)}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors',
                marketplace === mp.value
                  ? 'border-white/20 bg-white/10 text-white'
                  : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
              )}
            >
              <span>{mp.flag}</span>
              {mp.label}
            </button>
          ))}
        </div>
      </div>

      {/* ASIN + URL + Scrape button */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5 space-y-4">
        <div>
          <label className="text-sm font-medium text-white flex items-center gap-2">
            <Link2 className="h-4 w-4 text-gray-400" />
            Link do produktu
          </label>
          <div className="flex gap-2 mt-2">
            <input type="url" value={productUrl} onChange={(e) => handleUrlChange(e.target.value)}
              placeholder={URL_PLACEHOLDERS[marketplace] || 'https://...'} className={cn(inputCls, 'flex-1 px-4 py-3')} />
            {canScrape && (
              <button type="button" onClick={() => scrapeMutation.mutate()}
                disabled={scrapeMutation.isPending}
                className="flex items-center gap-2 rounded-lg border border-gray-600 px-4 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors disabled:opacity-50 shrink-0">
                {scrapeMutation.isPending ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Pobieram...</>
                ) : scraped ? (
                  <><CheckCircle2 className="h-4 w-4 text-green-400" /> Pobrano</>
                ) : (
                  <><Download className="h-4 w-4" /> Pobierz dane</>
                )}
              </button>
            )}
          </div>
          {SCRAPEABLE.has(marketplace) && productUrl.trim() && (
            <p className="text-xs text-gray-500 mt-1">
              Wklej link z {MARKETPLACES.find(m => m.value === marketplace)?.label} — pobierzemy dane automatycznie
            </p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium text-white flex items-center gap-2">
            <Package className="h-4 w-4 text-gray-400" />
            ASIN / ID produktu
          </label>
          <input type="text" value={asin} onChange={(e) => setAsin(e.target.value)}
            placeholder="np. B0XXXXXXX" className={cn(inputCls, 'mt-2 px-4 py-3')} />
          {asinWarning && (
            <p className="text-xs text-amber-400 mt-1">{asinWarning}</p>
          )}
        </div>
        {/* WHY: User needs to know why scrape button is missing for non-Allegro */}
        {productUrl.trim() && !SCRAPEABLE.has(marketplace) && (
          <p className="text-xs text-gray-500">
            Automatyczne pobieranie dostępne dla {MARKETPLACES.filter(m => SCRAPEABLE.has(m.value)).map(m => m.label).join(' i ')}. Dla {MARKETPLACES.find(m => m.value === marketplace)?.label || marketplace} — wpisz dane ręcznie.
          </p>
        )}
        <p className="text-xs text-gray-600">Podaj link, ASIN lub oba.</p>
      </div>

      {/* Product details (auto-opens after scrape) */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
        <button type="button" onClick={() => setShowDetails(!showDetails)}
          className="flex w-full items-center justify-between px-5 py-4 text-sm font-medium text-gray-400 hover:text-white transition-colors">
          <span>{scraped ? `Dane produktu (pobrane z ${MARKETPLACES.find(m => m.value === marketplace)?.label || 'marketplace'})` : 'Dane produktu (opcjonalne)'}</span>
          {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {showDetails && (
          <div className="border-t border-gray-800 px-5 py-4 space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-300">Tytuł</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="Nazwa produktu" className={cn(inputCls, 'mt-1')} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-300">Opis</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)}
                placeholder="Opis produktu" rows={3} className={cn(inputCls, 'mt-1')} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-300">Bullet Points</label>
              <div className="space-y-2 mt-1">
                {bullets.map((bullet, i) => (
                  <div key={i} className="flex gap-2">
                    <input type="text" value={bullet}
                      onChange={(e) => { const u = [...bullets]; u[i] = e.target.value; setBullets(u) }}
                      placeholder={`Punkt ${i + 1}`} className={cn(inputCls, 'flex-1')} />
                    {bullets.length > 1 && (
                      <button type="button" onClick={() => setBullets(bullets.filter((_, j) => j !== i))}
                        className="rounded-lg p-2 text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
                <button type="button" onClick={() => setBullets([...bullets, ''])}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors">
                  <Plus className="h-3 w-3" /> Dodaj punkt
                </button>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label className="text-sm font-medium text-gray-300">Marka</label>
                <input type="text" value={brand} onChange={(e) => setBrand(e.target.value)}
                  placeholder="Marka" className={cn(inputCls, 'mt-1')} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-300">Cena</label>
                <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)}
                  placeholder="29.99" className={cn(inputCls, 'mt-1')} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-300">Kategoria</label>
                <input type="text" value={category} onChange={(e) => setCategory(e.target.value)}
                  placeholder="Elektronika" className={cn(inputCls, 'mt-1')} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Submit */}
      <div className="flex gap-3">
        <button type="submit" disabled={importMutation.isPending || !canSubmit}
          className={cn(
            'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
            canSubmit ? 'bg-white text-black hover:bg-gray-200' : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          )}>
          <Upload className="h-4 w-4" />
          {importMutation.isPending ? 'Importowanie...' : 'Importuj produkt'}
        </button>
      </div>
    </form>
  )
}
