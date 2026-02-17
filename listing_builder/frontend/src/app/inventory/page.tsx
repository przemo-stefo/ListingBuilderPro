// frontend/src/app/inventory/page.tsx
// Purpose: Inventory tracking page with stock levels, reorder status, and supply metrics
// NOT for: Product editing or competitor tracking (those are separate pages)

'use client'

import { useState, useMemo, useCallback } from 'react'
import { useInventory } from '@/lib/hooks/useInventory'
import { GetInventoryParams, StockStatus } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { formatRelativeTime, formatNumber, truncate, cn, debounce } from '@/lib/utils'
import {
  RefreshCw,
  Package,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  Search,
} from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const INVENTORY_FAQ = [
  { question: 'Co oznaczaja kolory ilosci?', answer: 'Zielony = ilosc powyzej minimalnego zapasu (OK). Zolty = ilosc ponizej punktu zamowienia (trzeba zamowic). Czerwony = brak na stanie (pilne).' },
  { question: 'Co to jest "Zapas dni"?', answer: 'Zapas dni to szacunek na ile dni wystarczy aktualny stan magazynowy przy obecnym tempie sprzedazy. Ponizej 10 dni = czerwony alarm.' },
  { question: 'Co oznacza status "Nadmiar"?', answer: 'Nadmiar oznacza ze masz wiecej towaru niz optymalne. Moze to zamrazac kapital — rozważ promocje lub przesunięcie towaru miedzy marketplace.' },
  { question: 'Jak ustawic punkt ponownego zamowienia?', answer: 'Punkt zamowienia ustala sie w ustawieniach produktu. Gdy ilosc spadnie ponizej tej wartosci, system zmieni status na "Niski stan" i wysle alert (jesli wlaczony).' },
]

const MARKETPLACES = ['Amazon', 'eBay', 'Walmart', 'Shopify', 'Allegro']

const STOCK_STATUSES: { value: StockStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Wszystkie' },
  { value: 'in_stock', label: 'Na stanie' },
  { value: 'low_stock', label: 'Niski stan' },
  { value: 'out_of_stock', label: 'Brak' },
  { value: 'overstock', label: 'Nadmiar' },
]

// WHY: Color-coded status badge so users can instantly spot stock health
function StockStatusBadge({ status }: { status: StockStatus }) {
  const config: Record<StockStatus, { label: string; className: string }> = {
    in_stock: {
      label: 'Na stanie',
      className: 'bg-green-500/10 text-green-500 border-green-500/20',
    },
    low_stock: {
      label: 'Niski stan',
      className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    },
    out_of_stock: {
      label: 'Brak',
      className: 'bg-red-500/10 text-red-500 border-red-500/20',
    },
    overstock: {
      label: 'Nadmiar',
      className: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    },
  }

  const c = config[status]

  return (
    <Badge className={cn('text-xs', c.className)}>
      {c.label}
    </Badge>
  )
}

// WHY: Green = healthy stock, yellow = below reorder point, red = zero
function getQuantityColor(quantity: number, reorderPoint: number): string {
  if (quantity === 0) return 'text-red-500'
  if (quantity < reorderPoint) return 'text-yellow-500'
  return 'text-green-500'
}

// WHY: Green = 30+ days, yellow = 10-29 days, red = under 10 days of supply
function getDaysColor(days: number): string {
  if (days >= 30) return 'text-green-500'
  if (days >= 10) return 'text-yellow-500'
  return 'text-red-500'
}

export default function InventoryPage() {
  const [params, setParams] = useState<GetInventoryParams>({})
  const [searchInput, setSearchInput] = useState('')
  const { data, isLoading, error, refetch } = useInventory(params)

  // WHY: Debounce search to avoid spamming the API on every keystroke
  const debouncedSearch = useMemo(
    () =>
      debounce(((value: string) => {
        setParams((prev) => ({
          ...prev,
          search: value || undefined,
        }))
      }) as (...args: unknown[]) => unknown, 300),
    []
  )

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setSearchInput(value)
      debouncedSearch(value as unknown)
    },
    [debouncedSearch]
  )

  const handleMarketplaceFilter = (marketplace: string) => {
    setParams((prev) => ({
      ...prev,
      marketplace: marketplace === 'all' ? undefined : marketplace,
    }))
  }

  const handleStatusFilter = (status: string) => {
    setParams((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : (status as StockStatus),
    }))
  }

  const clearFilters = () => {
    setParams({})
    setSearchInput('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Magazyn</h1>
          <p className="text-gray-400 mt-2">
            Sledz stany magazynowe, punkt ponownego zamowienia i zapas dni na marketplace&apos;ach. Kontroluj ktore produkty wymagaja dostawy.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={cn('mr-2 h-4 w-4', isLoading && 'animate-spin')} />
          Odswiez
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <Package className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Wszystkie SKU</p>
                <p className="text-2xl font-bold text-white">
                  {data?.total ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-500/10 p-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Na stanie</p>
                <p className="text-2xl font-bold text-green-500">
                  {data?.in_stock_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-yellow-500/10 p-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Niski stan</p>
                <p className="text-2xl font-bold text-yellow-500">
                  {data?.low_stock_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-teal-500/10 p-2">
                <DollarSign className="h-5 w-5 text-teal-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Wartosc calkowita</p>
                <p className="text-2xl font-bold text-teal-500">
                  {data?.total_value != null
                    ? `$${formatNumber(data.total_value)}`
                    : '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Top row: Marketplace + Search */}
            <div className="flex flex-col gap-4 md:flex-row md:items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400 whitespace-nowrap">Marketplace:</span>
                <div className="flex gap-2 overflow-x-auto">
                  <Button
                    variant={!params.marketplace ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleMarketplaceFilter('all')}
                  >
                    Wszystkie
                  </Button>
                  {MARKETPLACES.map((mp) => (
                    <Button
                      key={mp}
                      variant={params.marketplace === mp ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleMarketplaceFilter(mp)}
                    >
                      {mp}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 md:ml-auto">
                <Search className="h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Szukaj SKU lub produktu..."
                  value={searchInput}
                  onChange={handleSearchChange}
                  className="w-64"
                />
              </div>
            </div>

            {/* Bottom row: Stock Status */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400 whitespace-nowrap">Status:</span>
              <div className="flex gap-2 overflow-x-auto">
                {STOCK_STATUSES.map((s) => (
                  <Button
                    key={s.value}
                    variant={
                      (s.value === 'all' && !params.status) || params.status === s.value
                        ? 'default'
                        : 'outline'
                    }
                    size="sm"
                    onClick={() => handleStatusFilter(s.value)}
                  >
                    {s.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      {isLoading ? (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-700 rounded animate-pulse" />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-500">Blad ladowania magazynu</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-400 mb-4">
              {error instanceof Error ? error.message : 'Cos poszlo nie tak'}
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              Ponow
            </Button>
          </CardContent>
        </Card>
      ) : data && data.items.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">SKU</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Produkt</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Marketplace</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Ilosc</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Min. zapas</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Zapas dni</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Cena jedn.</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Wartosc</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Ostatnia dostawa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-mono text-white">
                        {item.sku}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300" title={item.product_title}>
                        {truncate(item.product_title, 40)}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="secondary">{item.marketplace}</Badge>
                      </td>
                      <td className={cn(
                        'px-6 py-4 text-sm font-mono',
                        getQuantityColor(item.quantity, item.reorder_point)
                      )}>
                        {formatNumber(item.quantity)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300 font-mono">
                        {formatNumber(item.reorder_point)}
                      </td>
                      <td className={cn(
                        'px-6 py-4 text-sm font-mono',
                        getDaysColor(item.days_of_supply)
                      )}>
                        {item.days_of_supply}d
                      </td>
                      <td className="px-6 py-4">
                        <StockStatusBadge status={item.status} />
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        ${item.unit_cost.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        ${formatNumber(item.total_value)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400">
                        {formatRelativeTime(item.last_restocked)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-400">Brak pozycji magazynowych pasujacych do filtrow</p>
            <Button
              className="mt-4"
              variant="outline"
              onClick={clearFilters}
            >
              Wyczysc filtry
            </Button>
          </CardContent>
        </Card>
      )}

      <FaqSection
        title="Najczesciej zadawane pytania"
        subtitle="Magazyn i zapasy"
        items={INVENTORY_FAQ}
      />
    </div>
  )
}
