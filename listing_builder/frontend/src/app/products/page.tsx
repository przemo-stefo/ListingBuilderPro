// frontend/src/app/products/page.tsx
// Purpose: Product list page with filters, search, and bulk actions
// NOT for: Single product details (that's [id]/page.tsx)

'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useProducts, useDeleteProduct } from '@/lib/hooks/useProducts'
import { ProductFilters } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { formatRelativeTime, getStatusColor, getStatusLabel, truncate, cn } from '@/lib/utils'
import { Search, Trash2, ExternalLink, Sparkles } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const PRODUCTS_FAQ = [
  { question: 'Jak importowac produkty?', answer: 'Kliknij "Importuj produkty" w prawym gornym rogu. Mozesz wkleic URL z Allegro, przeslac plik CSV lub polaczyc sie z API Allegro. System automatycznie pobierze dane o produkcie.' },
  { question: 'Co oznaczaja statusy produktow?', answer: 'Imported = czekaja na optymalizacje AI. Optimized = przetworzone przez AI z nowym tytulem i opisem. Published = wyeksportowane na marketplace. Failed = problem podczas przetwarzania.' },
  { question: 'Czy moge usunac produkt?', answer: 'Tak, kliknij ikone kosza przy produkcie. Usuniecie jest trwale — produkt zostanie usuniety z systemu wraz z historia optymalizacji.' },
  { question: 'Jak filtrowac produkty?', answer: 'Uzyj paska wyszukiwania aby znalezc produkt po nazwie, ASIN lub marce. Przyciski statusu filtruja wedlug etapu przetwarzania.' },
]

export default function ProductsPage() {
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

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setFilters((prev) => ({ ...prev, search: query, page: 1 }))
  }

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
            const description = product.description_optimized || product.description_original

            return (
              <Card key={product.id} className="hover:border-gray-600 transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
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
                      <Link href={`/optimize?prefill=${encodeURIComponent(JSON.stringify({ product_title: title, brand: product.brand || '', keywords: [] }))}`}>
                        <Button variant="ghost" size="icon" title="Optymalizuj">
                          <Sparkles className="h-4 w-4 text-blue-400" />
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

          {/* Pagination */}
          {data.total_pages > (filters.page || 1) && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
              >
                Zaladuj wiecej
              </Button>
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
