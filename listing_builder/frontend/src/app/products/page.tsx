// frontend/src/app/products/page.tsx
// Purpose: Product list page with filters, search, and bulk actions
// NOT for: Single product details (that's [id]/page.tsx)

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useProducts, useDeleteProduct } from '@/lib/hooks/useProducts'
import { ProductFilters } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { formatRelativeTime, getStatusColor, truncate, cn } from '@/lib/utils'
import { Search, Trash2, ExternalLink, Filter } from 'lucide-react'

export default function ProductsPage() {
  const [filters, setFilters] = useState<ProductFilters>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  })

  const [searchQuery, setSearchQuery] = useState('')
  const { data, isLoading, error } = useProducts(filters)
  const deleteProduct = useDeleteProduct()

  // Handle search with debounce
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setFilters((prev) => ({ ...prev, search: query, page: 1 }))
  }

  // Handle status filter
  const handleStatusFilter = (status: string) => {
    setFilters((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : status as ProductFilters['status'],
      page: 1,
    }))
  }

  // Handle delete
  const handleDelete = async (id: string) => {
    if (confirm('Czy na pewno chcesz usunac ten produkt?')) {
      await deleteProduct.mutateAsync(id)
    }
  }

  const statusFilters = [
    { label: 'Wszystkie', value: 'all' },
    { label: 'Oczekujace', value: 'pending' },
    { label: 'Zoptymalizowane', value: 'optimized' },
    { label: 'Opublikowane', value: 'published' },
    { label: 'Bledy', value: 'error' },
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
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Szukaj produktow..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Status Filter */}
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
          {data.items.map((product) => (
            <Card key={product.id} className="hover:border-gray-600 transition-colors">
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Link
                        href={`/products/${product.id}`}
                        className="text-lg font-semibold text-white hover:underline"
                      >
                        {truncate(product.title, 80)}
                      </Link>
                      <Badge className={cn('text-xs', getStatusColor(product.status))}>
                        {product.status}
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-400 mb-3">
                      {truncate(product.description || 'Brak opisu', 150)}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      {product.asin && (
                        <span>ASIN: {product.asin}</span>
                      )}
                      {product.brand && (
                        <span>Marka: {product.brand}</span>
                      )}
                      {product.marketplace && (
                        <span>Rynek: {product.marketplace}</span>
                      )}
                      {product.optimization_score && (
                        <span className="text-green-500">
                          Ocena: {Math.round(product.optimization_score)}%
                        </span>
                      )}
                      <span>{formatRelativeTime(product.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link href={`/products/${product.id}`}>
                      <Button variant="ghost" size="icon">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(product.id)}
                      disabled={deleteProduct.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Pagination */}
          {data.has_more && (
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
    </div>
  )
}
