// frontend/src/app/optimize/components/BatchTab.tsx
// Purpose: Batch import tab — CSV upload, paste, or Allegro URLs → optimize multiple products
// NOT for: Single-product optimization (that's SingleTab.tsx)

'use client'

import { useState, useRef } from 'react'
import {
  Upload,
  ClipboardPaste,
  Link2,
  Loader2,
  Sparkles,
  Trash2,
  Search,
  Zap,
  Target,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useBatchOptimizer, useScrapeForOptimizer } from '@/lib/hooks/useOptimizer'
import { parseOptimizerCSV, parsePasteText } from '@/lib/utils/csvParser'
import BatchResults from './BatchResults'
import type {
  ParsedBatchProduct,
  OptimizerRequest,
  BatchOptimizerResponse,
} from '@/lib/types'

type InputMode = 'csv' | 'paste' | 'urls'

// WHY: Marketplace options match what the n8n workflow supports
const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

export default function BatchTab() {
  const [inputMode, setInputMode] = useState<InputMode>('csv')
  const [marketplace, setMarketplace] = useState('amazon_de')
  const [mode, setMode] = useState<'aggressive' | 'standard'>('aggressive')

  // Parsed products ready for preview
  const [products, setProducts] = useState<ParsedBatchProduct[]>([])
  // Batch results after optimization
  const [batchResults, setBatchResults] = useState<BatchOptimizerResponse | null>(null)

  // Input state for paste and URLs modes
  const [pasteText, setPasteText] = useState('')
  const [urlsText, setUrlsText] = useState('')
  const [sharedKeywords, setSharedKeywords] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Hooks
  const batchMutation = useBatchOptimizer()
  const scrapeMutation = useScrapeForOptimizer()

  const isLoading = batchMutation.isPending
  const isScraping = scrapeMutation.isPending

  // WHY: CSV upload — read file content and parse with Papa Parse
  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (ev) => {
      const text = ev.target?.result as string
      const parsed = parseOptimizerCSV(text)
      setProducts(parsed)
      setBatchResults(null)
    }
    reader.readAsText(file)

    // WHY: Reset file input so the same file can be re-uploaded
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // WHY: Parse pasted text into products
  const handleParsePaste = () => {
    const parsed = parsePasteText(pasteText)
    setProducts(parsed)
    setBatchResults(null)
  }

  // WHY: Scrape Allegro URLs, then merge with shared keywords
  const handleScrapeUrls = () => {
    const urls = urlsText
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.length > 0)

    if (urls.length === 0) return

    const keywords = sharedKeywords
      .split('\n')
      .map((k) => k.trim())
      .filter((k) => k.length > 0)

    scrapeMutation.mutate(urls, {
      onSuccess: (data) => {
        const scraped: ParsedBatchProduct[] = data.products
          .filter((p) => p.title)
          .map((p) => ({
            product_title: (p.title as string) || '',
            brand: (p.brand as string) || (p.parameters as Record<string, string>)?.['Marka'] || '',
            keywords,
          }))
        setProducts(scraped)
        setBatchResults(null)
      },
    })
  }

  // WHY: Convert ParsedBatchProduct[] → OptimizerRequest[] with shared marketplace/mode
  const handleOptimizeAll = () => {
    const requests: OptimizerRequest[] = products.map((p) => ({
      product_title: p.product_title,
      brand: p.brand,
      product_line: p.product_line,
      keywords: p.keywords.map((k) => ({ phrase: k, search_volume: 0 })),
      marketplace,
      mode,
      asin: p.asin,
      category: p.category,
    }))

    batchMutation.mutate(
      { products: requests },
      {
        onSuccess: (data) => {
          setBatchResults(data)
        },
      }
    )
  }

  const removeProduct = (index: number) => {
    setProducts((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-6">
      {/* Input mode selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Importuj produkty</CardTitle>
          <CardDescription>Wybierz sposob dodania produktow do zbiorowej optymalizacji</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Sub-mode buttons */}
          <div className="flex gap-2">
            {[
              { id: 'csv' as InputMode, label: 'Wgraj CSV', icon: Upload },
              { id: 'paste' as InputMode, label: 'Wklej', icon: ClipboardPaste },
              { id: 'urls' as InputMode, label: 'URLe', icon: Link2 },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setInputMode(m.id)}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                  inputMode === m.id
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                )}
              >
                <m.icon className="h-4 w-4" />
                {m.label}
              </button>
            ))}
          </div>

          {/* CSV Upload */}
          {inputMode === 'csv' && (
            <div className="space-y-3">
              <div className="rounded-lg border border-dashed border-gray-700 p-6 text-center">
                <Upload className="mx-auto mb-2 h-8 w-8 text-gray-500" />
                <p className="mb-2 text-sm text-gray-400">
                  Wgraj CSV z kolumnami: product_title, brand, keywords
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleCSVUpload}
                  className="hidden"
                  id="csv-upload"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Wybierz plik
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                Slowa kluczowe w CSV: rozdzielone kreska (keyword1|keyword2|keyword3)
              </p>
            </div>
          )}

          {/* Paste */}
          {inputMode === 'paste' && (
            <div className="space-y-3">
              <textarea
                value={pasteText}
                onChange={(e) => setPasteText(e.target.value)}
                placeholder={
                  'Silicone Kitchen Utensil Set|ZULAY|kitchen utensil set,cooking utensils,silicone spatula\nStainless Steel Pan 28cm|ZWILLING|stainless steel pan,non stick pan,cookware'
                }
                rows={6}
                className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  Format: tytul|marka|keyword1,keyword2,keyword3
                </p>
                <Button variant="outline" size="sm" onClick={handleParsePaste}>
                  Parsuj produkty
                </Button>
              </div>
            </div>
          )}

          {/* URLs */}
          {inputMode === 'urls' && (
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-gray-400">URLe Allegro (po jednym w linii)</label>
                <textarea
                  value={urlsText}
                  onChange={(e) => setUrlsText(e.target.value)}
                  placeholder={
                    'https://allegro.pl/oferta/product-1-id\nhttps://allegro.pl/oferta/product-2-id'
                  }
                  rows={4}
                  className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">
                  Wspolne slowa kluczowe (po jednym w linii — dla wszystkich produktow)
                </label>
                <textarea
                  value={sharedKeywords}
                  onChange={(e) => setSharedKeywords(e.target.value)}
                  placeholder={'kitchen utensil set\ncooking utensils\nsilicone spatula'}
                  rows={4}
                  className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleScrapeUrls}
                  disabled={isScraping}
                >
                  {isScraping ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="mr-2 h-4 w-4" />
                  )}
                  {isScraping ? 'Scrapowanie...' : 'Scrapuj i podejrzyj'}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Marketplace & Mode — shared for all products */}
      {products.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-gray-400" />
              <CardTitle className="text-lg">Cel i tryb</CardTitle>
            </div>
            <CardDescription>Zastosowane do wszystkich {products.length} produktow</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm text-gray-400">Marketplace</label>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                {MARKETPLACES.map((mp) => (
                  <button
                    key={mp.id}
                    onClick={() => setMarketplace(mp.id)}
                    className={cn(
                      'rounded-lg border px-3 py-2 text-sm transition-colors',
                      marketplace === mp.id
                        ? 'border-white bg-white/5 text-white'
                        : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                    )}
                  >
                    <span className="mr-1 text-xs">{mp.flag}</span>
                    {mp.name}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm text-gray-400">Tryb optymalizacji</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setMode('aggressive')}
                  className={cn(
                    'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                    mode === 'aggressive'
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600'
                  )}
                >
                  <Zap className="h-4 w-4" />
                  Agresywny
                </button>
                <button
                  onClick={() => setMode('standard')}
                  className={cn(
                    'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                    mode === 'standard'
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600'
                  )}
                >
                  <Target className="h-4 w-4" />
                  Standardowy
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview table */}
      {products.length > 0 && !batchResults && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                Podglad ({products.length} {products.length === 1 ? 'produkt' : products.length < 5 ? 'produkty' : 'produktow'})
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setProducts([])}
              >
                Wyczysc
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-left text-gray-500">
                    <th className="pb-2 pr-4">#</th>
                    <th className="pb-2 pr-4">Tytul produktu</th>
                    <th className="pb-2 pr-4">Marka</th>
                    <th className="pb-2 pr-4">Slowa kluczowe</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 text-gray-500">{i + 1}</td>
                      <td className="py-2 pr-4 text-white">{p.product_title}</td>
                      <td className="py-2 pr-4 text-gray-300">{p.brand}</td>
                      <td className="py-2 pr-4">
                        <div className="flex flex-wrap gap-1">
                          {p.keywords.slice(0, 3).map((k, ki) => (
                            <Badge key={ki} variant="secondary" className="text-[10px]">
                              {k}
                            </Badge>
                          ))}
                          {p.keywords.length > 3 && (
                            <Badge variant="secondary" className="text-[10px] text-gray-500">
                              +{p.keywords.length - 3}
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => removeProduct(i)}
                          className="text-gray-500 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Optimize All button */}
      {products.length > 0 && !batchResults && (
        <div className="flex items-center gap-3">
          <Button onClick={handleOptimizeAll} disabled={isLoading} size="lg">
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            {isLoading
              ? `Przetwarzanie ${products.length} produktow...`
              : `Optymalizuj wszystkie (${products.length})`}
          </Button>
          {isLoading && (
            <span className="text-xs text-gray-500">
              To moze chwile potrwac — ~5s na produkt
            </span>
          )}
        </div>
      )}

      {/* Batch results */}
      {batchResults && (
        <BatchResults
          response={batchResults}
          onReset={() => {
            setBatchResults(null)
            setProducts([])
          }}
        />
      )}
    </div>
  )
}
