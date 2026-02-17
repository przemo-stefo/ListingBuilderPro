// frontend/src/app/products/import/components/SingleImport.tsx
// Purpose: Single product import form (ASIN/URL/manual + URL scraping)
// NOT for: Batch import or optimization

'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
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
  } catch { /* not a valid URL */ }
  return null
}

// WHY: Only Allegro scraping is implemented — others need different scrapers
const SCRAPEABLE = new Set(['allegro'])

export default function SingleImport() {
  const router = useRouter()
  const { toast } = useToast()

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
  const [scraped, setScraped] = useState(false)

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
      const product = {
        source_platform: marketplace,
        source_id: asin || 'manual',
        source_url: productUrl || undefined,
        title: title || asin || productUrl || 'Produkt bez nazwy',
        asin: asin || undefined,
        brand: brand || undefined,
        price: price ? parseFloat(price) : undefined,
        category: category || undefined,
        description: description || undefined,
        bullet_points: bullets.filter(b => b.trim()),
      }
      return await importSingleProduct(product)
    },
    onSuccess: () => {
      toast({ title: 'Produkt zaimportowany', description: 'Produkt został dodany do systemu' })
      router.push('/products')
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd importu', description: error.message, variant: 'destructive' })
    },
  })

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
              placeholder="https://allegro.pl/oferta/..." className={cn(inputCls, 'flex-1 px-4 py-3')} />
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
              Wklej link z Allegro — pobierzemy tytuł, cenę, markę i opis automatycznie
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
        </div>
        <p className="text-xs text-gray-600">Podaj link, ASIN lub oba.</p>
      </div>

      {/* Product details (auto-opens after scrape) */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
        <button type="button" onClick={() => setShowDetails(!showDetails)}
          className="flex w-full items-center justify-between px-5 py-4 text-sm font-medium text-gray-400 hover:text-white transition-colors">
          <span>{scraped ? 'Dane produktu (pobrane z Allegro)' : 'Dane produktu (opcjonalne)'}</span>
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
