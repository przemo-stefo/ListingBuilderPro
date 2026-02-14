// frontend/src/app/products/import/page.tsx
// Purpose: Product import — ASIN/URL first, optional manual details
// NOT for: Product editing, optimization, or monitoring

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { importSingleProduct } from '@/lib/api/import'
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
  ArrowLeft,
} from 'lucide-react'

const MARKETPLACES = [
  { value: 'amazon', label: 'Amazon', flag: '📦' },
  { value: 'allegro', label: 'Allegro', flag: '🇵🇱' },
  { value: 'ebay', label: 'eBay', flag: '🏷️' },
  { value: 'kaufland', label: 'Kaufland', flag: '🇩🇪' },
]

export default function ImportPage() {
  const router = useRouter()
  const { toast } = useToast()

  // WHY: Primary fields — what the user actually wants to enter first
  const [marketplace, setMarketplace] = useState('amazon')
  const [asin, setAsin] = useState('')
  const [productUrl, setProductUrl] = useState('')

  // WHY: Optional details — collapsed by default, user rarely needs these
  const [showDetails, setShowDetails] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [bullets, setBullets] = useState<string[]>([''])
  const [brand, setBrand] = useState('')
  const [price, setPrice] = useState('')
  const [category, setCategory] = useState('')

  const importMutation = useMutation({
    mutationFn: async () => {
      // WHY: Build payload matching backend ProductImport schema
      const product = {
        source_platform: marketplace,
        source_id: asin || 'manual',
        source_url: productUrl || undefined,
        title: title || asin || productUrl || 'Untitled Product',
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
      toast({
        title: 'Produkt zaimportowany',
        description: 'Produkt został dodany do systemu',
      })
      router.push('/products')
    },
    onError: (error: Error) => {
      toast({
        title: 'Błąd importu',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const canSubmit = asin.trim() || productUrl.trim() || title.trim()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) {
      toast({
        title: 'Brakujące dane',
        description: 'Podaj ASIN, link do produktu lub tytuł',
        variant: 'destructive',
      })
      return
    }
    importMutation.mutate()
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Wróć
        </button>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Upload className="h-6 w-6 text-gray-400" />
          Importuj Produkt
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Dodaj produkt do systemu podając ASIN, link lub dane ręcznie
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Marketplace selector */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
          <label className="text-sm font-medium text-white mb-3 block">
            Marketplace
          </label>
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

        {/* ASIN + URL — primary inputs */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5 space-y-4">
          <div>
            <label className="text-sm font-medium text-white flex items-center gap-2">
              <Package className="h-4 w-4 text-gray-400" />
              ASIN / ID produktu
            </label>
            <input
              type="text"
              value={asin}
              onChange={(e) => setAsin(e.target.value)}
              placeholder="np. B0XXXXXXX"
              className="mt-2 w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-gray-500"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-white flex items-center gap-2">
              <Link2 className="h-4 w-4 text-gray-400" />
              Link do produktu
            </label>
            <input
              type="url"
              value={productUrl}
              onChange={(e) => setProductUrl(e.target.value)}
              placeholder="https://www.amazon.de/dp/B0XXXXXXX"
              className="mt-2 w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-gray-500"
            />
          </div>

          <p className="text-xs text-gray-600">
            Podaj ASIN, link lub oba. Dane produktu możesz uzupełnić później.
          </p>
        </div>

        {/* Optional details — collapsed */}
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="flex w-full items-center justify-between px-5 py-4 text-sm font-medium text-gray-400 hover:text-white transition-colors"
          >
            <span>Dane produktu (opcjonalne)</span>
            {showDetails ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>

          {showDetails && (
            <div className="border-t border-gray-800 px-5 py-4 space-y-4">
              {/* Title */}
              <div>
                <label className="text-sm font-medium text-gray-300">Tytuł</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Nazwa produktu"
                  className="mt-1 w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* Description */}
              <div>
                <label className="text-sm font-medium text-gray-300">Opis</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Opis produktu"
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* Bullet Points */}
              <div>
                <label className="text-sm font-medium text-gray-300">Bullet Points</label>
                <div className="space-y-2 mt-1">
                  {bullets.map((bullet, i) => (
                    <div key={i} className="flex gap-2">
                      <input
                        type="text"
                        value={bullet}
                        onChange={(e) => {
                          const updated = [...bullets]
                          updated[i] = e.target.value
                          setBullets(updated)
                        }}
                        placeholder={`Punkt ${i + 1}`}
                        className="flex-1 rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                      />
                      {bullets.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setBullets(bullets.filter((_, j) => j !== i))}
                          className="rounded-lg p-2 text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => setBullets([...bullets, ''])}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
                  >
                    <Plus className="h-3 w-3" />
                    Dodaj punkt
                  </button>
                </div>
              </div>

              {/* Brand, Price, Category */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="text-sm font-medium text-gray-300">Marka</label>
                  <input
                    type="text"
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    placeholder="Brand"
                    className="mt-1 w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-300">Cena</label>
                  <input
                    type="number"
                    step="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="29.99"
                    className="mt-1 w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-300">Kategoria</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="Electronics"
                    className="mt-1 w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={importMutation.isPending || !canSubmit}
            className={cn(
              'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
              canSubmit
                ? 'bg-white text-black hover:bg-gray-200'
                : 'bg-gray-800 text-gray-500 cursor-not-allowed'
            )}
          >
            <Upload className="h-4 w-4" />
            {importMutation.isPending ? 'Importowanie...' : 'Importuj produkt'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-lg border border-gray-700 px-4 py-3 text-sm text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
          >
            Anuluj
          </button>
        </div>
      </form>
    </div>
  )
}
