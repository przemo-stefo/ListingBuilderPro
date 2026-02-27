// frontend/src/app/products/page.tsx
// Purpose: Product list page with filters, search, and bulk actions
// NOT for: Single product details (that's [id]/page.tsx)

'use client'

import { useState, useCallback, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useProducts, useDeleteProduct } from '@/lib/hooks/useProducts'
import { ProductFilters } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { formatRelativeTime, getStatusColor, getStatusLabel, truncate, cn } from '@/lib/utils'
import { Search, Trash2, ExternalLink, Sparkles, ChevronLeft, ChevronRight, ArrowRight, ArrowRightLeft, Package, Globe } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const PRODUCTS_FAQ = [
  { question: 'Jak importowac produkty?', answer: 'Kliknij "Importuj produkty" w prawym gornym rogu. Mozesz wkleic URL z Allegro, przeslac plik CSV lub polaczyc sie z API Allegro. System automatycznie pobierze dane o produkcie.' },
  { question: 'Co oznaczaja statusy produktow?', answer: 'Imported = czekaja na optymalizacje AI. Optimized = przetworzone przez AI z nowym tytulem i opisem. Published = wyeksportowane na marketplace. Failed = problem podczas przetwarzania.' },
  { question: 'Czy moge usunac produkt?', answer: 'Tak, kliknij ikone kosza przy produkcie. Usuniecie jest trwale — produkt zostanie usuniety z systemu wraz z historia optymalizacji.' },
  { question: 'Jak filtrowac produkty?', answer: 'Uzyj paska wyszukiwania aby znalezc produkt po nazwie, ASIN lub marce. Przyciski statusu filtruja wedlug etapu przetwarzania.' },
]

// WHY: Suspense boundary required for useSearchParams() in Next.js 14 App Router
export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="space-y-6"><h1 className="text-3xl font-bold text-white">Produkty</h1></div>}>
      <ProductsContent />
    </Suspense>
  )
}

function ProductsContent() {
  // WHY: Read ?status= from URL so dashboard "Do optymalizacji" link pre-filters the list
  const searchParams = useSearchParams()
  const initialStatus = searchParams.get('status') as ProductFilters['status'] | null

  const [filters, setFilters] = useState<ProductFilters>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
    status: initialStatus || undefined,
  })

  const [searchQuery, setSearchQuery] = useState('')
  const { data, isLoading, error } = useProducts(filters)
  const deleteProduct = useDeleteProduct()

  // WHY: Debounce search — only hit API after 300ms of no typing
  const debounceRef = useRef<NodeJS.Timeout | null>(null)
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: query, page: 1 }))
    }, 300)
  }, [])

  const handleStatusFilter = (status: string) => {
    setFilters((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : status as ProductFilters['status'],
      page: 1,
    }))
  }

  const handleDelete = async (id: number) => {
    if (confirm('Czy na pewno chcesz usunac ten produkt?')) {
      await deleteProduct.mutateAsync(String(id))
    }
  }

  const statusFilters = [
    { label: 'Wszystkie', value: 'all' },
    { label: 'Zaimportowane', value: 'imported' },
    { label: 'Zoptymalizowane', value: 'optimized' },
    { label: 'Wyeksportowane', value: 'published' },
    { label: 'Bledy', value: 'failed' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Produkty</h1>
          <p className="text-gray-400 mt-2">
            Zarzadzaj swoimi produktami. Tutaj zobaczysz wszystkie zaimportowane oferty — ich status, ocene AI i akcje.
          </p>
        </div>
        <Link href="/products/import">
          <Button>Importuj produkty</Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Szukaj produktow..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 overflow-x-auto">
              {statusFilters.map((status) => (
                <Button
                  key={status.value}
                  variant={filters.status === status.value || (!filters.status && status.value === 'all') ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleStatusFilter(status.value)}
                >
                  {status.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* WHY: Action bar when viewing imported products — nudge user to optimize */}
      {!isLoading && data && filters.status === 'imported' && data.items.length > 0 && (
        <Link
          href="/optimize"
          className="flex items-center justify-between rounded-lg border border-blue-800 bg-blue-900/20 p-4 hover:bg-blue-900/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-blue-400" />
            <div>
              <p className="text-sm font-medium text-blue-300">
                {data.total} {data.total === 1 ? 'produkt czeka' : data.total < 5 ? 'produkty czekaja' : 'produktow czeka'} na optymalizacje
              </p>
              <p className="text-xs text-blue-500 mt-0.5">Kliknij aby przejsc do Optymalizatora</p>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-blue-400" />
        </Link>
      )}

      {/* Products List */}
      {isLoading ? (
        <div className="grid gap-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-20 bg-gray-700 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-500">Blad ladowania produktow</CardTitle>
          </CardHeader>
        </Card>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-4">
          {data.items.map((product) => {
            // WHY: Backend has title_original + title_optimized, show optimized if available
            const title = product.title_optimized || product.title_original || 'Bez tytulu'
            // WHY: Description may contain HTML from optimizer — strip tags for preview
            const rawDesc = product.description_optimized || product.description_original
            const description = rawDesc ? rawDesc.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim() : null

            return (
              <Card key={product.id} className="hover:border-gray-600 transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    {/* WHY: Product thumbnail — shows first image or placeholder icon */}
                    <div className="h-16 w-16 shrink-0 rounded-lg overflow-hidden bg-gray-800 flex items-center justify-center">
                      {product.images?.length > 0 ? (
                        <img src={product.images[0]} alt="" loading="lazy" className="h-full w-full object-cover" />
                      ) : (
                        <Package className="h-6 w-6 text-gray-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Link
                          href={`/products/${product.id}`}
                          className="text-lg font-semibold text-white hover:underline"
                        >
                          {truncate(title, 80)}
                        </Link>
                        <Badge className={cn('text-xs', getStatusColor(product.status))}>
                          {getStatusLabel(product.status)}
                        </Badge>
                      </div>

                      <p className="text-sm text-gray-400 mb-3">
                        {truncate(description || 'Brak opisu', 150)}
                      </p>

                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        {product.source_id && product.source_id !== 'manual' && (
                          <span>ID: {product.source_id}</span>
                        )}
                        {product.brand && (
                          <span>Marka: {product.brand}</span>
                        )}
                        {product.source_platform && (
                          <span>Zrodlo: {product.source_platform}</span>
                        )}
                        {product.optimization_score && (
                          <span className="text-green-500">
                            Ocena: {Math.round(product.optimization_score)}%
                          </span>
                        )}
                        <span>{formatRelativeTime(product.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      {/* WHY: Link to live listing — lets user see the actual offer on marketplace */}
                      {product.source_url && (
                        <a href={product.source_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon" title="Zobacz ofertę na marketplace">
                            <Globe className="h-4 w-4 text-green-400" />
                          </Button>
                        </a>
                      )}
                      <Link href={`/optimize?prefill=${encodeURIComponent(title)}&product_id=${product.id}`}>
                        <Button variant="ghost" size="icon" title="Optymalizuj">
                          <Sparkles className="h-4 w-4 text-blue-400" />
                        </Button>
                      </Link>
                      <Link href={`/converter?title=${encodeURIComponent(title)}&product_id=${product.id}`}>
                        <Button variant="ghost" size="icon" title="Konwertuj na inny marketplace">
                          <ArrowRightLeft className="h-4 w-4 text-amber-400" />
                        </Button>
                      </Link>
                      <Link href={`/products/${product.id}`}>
                        <Button variant="ghost" size="icon" title="Szczegoly">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(product.id)}
                        disabled={deleteProduct.isPending}
                        title="Usun"
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}

          {/* WHY: Numbered pagination — user sees where they are and can jump to any page */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="icon"
                disabled={(filters.page || 1) <= 1}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) - 1 }))}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              {Array.from({ length: data.total_pages }, (_, i) => i + 1)
                .filter((p) => {
                  const current = filters.page || 1
                  return p === 1 || p === data.total_pages || Math.abs(p - current) <= 1
                })
                .reduce<(number | 'dots')[]>((acc, p, i, arr) => {
                  if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('dots')
                  acc.push(p)
                  return acc
                }, [])
                .map((item, i) =>
                  item === 'dots' ? (
                    <span key={`dots-${i}`} className="px-1 text-gray-500">...</span>
                  ) : (
                    <Button
                      key={item}
                      variant={(filters.page || 1) === item ? 'default' : 'outline'}
                      size="icon"
                      onClick={() => setFilters((prev) => ({ ...prev, page: item as number }))}
                    >
                      {item}
                    </Button>
                  )
                )}
              <Button
                variant="outline"
                size="icon"
                disabled={(filters.page || 1) >= data.total_pages}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <span className="ml-2 text-sm text-gray-500">
                {data.total} {data.total === 1 ? 'produkt' : data.total < 5 ? 'produkty' : 'produktow'}
              </span>
            </div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-400">Brak produktow</p>
            <Link href="/products/import">
              <Button className="mt-4">Importuj pierwszy produkt</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      <FaqSection
        title="Najczesciej zadawane pytania"
        subtitle="Zarzadzanie produktami"
        items={PRODUCTS_FAQ}
      />
    </div>
  )
}
