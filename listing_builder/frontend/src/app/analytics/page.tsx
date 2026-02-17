// frontend/src/app/analytics/page.tsx
// Purpose: Analytics page with sales performance, revenue charts, and top products
// NOT for: Product editing or inventory management (those are separate pages)

'use client'

import { useState } from 'react'
import { useAnalytics } from '@/lib/hooks/useAnalytics'
import { GetAnalyticsParams } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatNumber, truncate, cn } from '@/lib/utils'
import {
  RefreshCw,
  DollarSign,
  ShoppingCart,
  TrendingUp,
  BarChart3,
} from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const ANALYTICS_FAQ = [
  { question: 'Jak odczytywac wykresy?', answer: 'Wykres "Przychod wg marketplace" pokazuje udzial kazdego kanalu w sprzedazy. Wykres "Trend przychodow" pokazuje jak zmienia sie przychod miesieczny — najezdzaj na slupki aby zobaczyc szczegoly.' },
  { question: 'Co to jest konwersja?', answer: 'Konwersja to procent odwiedzajacych Twoj listing, ktorzy dokonali zakupu. Powyzej 5% to swietny wynik, ponizej 2% sugeruje potrzebe optymalizacji.' },
  { question: 'Jak filtrowac dane?', answer: 'Uzyj przyciskow "Okres" aby wybrac zakres czasu (7 dni, 30 dni, 90 dni, 12 mies.) i "Marketplace" aby zobaczyc dane z konkretnego kanalu sprzedazy.' },
]

const MARKETPLACES = ['Amazon', 'eBay', 'Walmart', 'Shopify', 'Allegro']
const PERIODS: { value: GetAnalyticsParams['period']; label: string }[] = [
  { value: '7d', label: '7 dni' },
  { value: '30d', label: '30 dni' },
  { value: '90d', label: '90 dni' },
  { value: '12m', label: '12 mies.' },
]

// WHY: Each marketplace gets a distinct color so horizontal bars are easy to compare
const MARKETPLACE_COLORS: Record<string, string> = {
  Amazon: 'bg-orange-500',
  eBay: 'bg-blue-500',
  Walmart: 'bg-green-500',
  Shopify: 'bg-emerald-400',
  Allegro: 'bg-red-500',
}

// WHY: Green = strong conversion, yellow = average, red = weak
function getConversionColor(rate: number): string {
  if (rate >= 5) return 'text-green-500'
  if (rate >= 2) return 'text-yellow-500'
  return 'text-red-500'
}

export default function AnalyticsPage() {
  const [params, setParams] = useState<GetAnalyticsParams>({ period: '30d' })
  const { data, isLoading, error, refetch } = useAnalytics(params)

  const handleMarketplaceFilter = (marketplace: string) => {
    setParams((prev) => ({
      ...prev,
      marketplace: marketplace === 'all' ? undefined : marketplace,
    }))
  }

  const handlePeriodFilter = (period: GetAnalyticsParams['period']) => {
    setParams((prev) => ({ ...prev, period }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analityka</h1>
          <p className="text-gray-400 mt-2">
            Wyniki sprzedazowe, rozklad przychodow i najpopularniejsze produkty. Filtruj po marketplace i okresie.
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

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Period selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400 whitespace-nowrap">Okres:</span>
              <div className="flex gap-2">
                {PERIODS.map((p) => (
                  <Button
                    key={p.value}
                    variant={params.period === p.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handlePeriodFilter(p.value)}
                  >
                    {p.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Marketplace selector */}
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
          </div>
        </CardContent>
      </Card>

      {/* Loading skeleton */}
      {isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardContent className="pt-6">
                  <div className="h-16 bg-gray-700 rounded animate-pulse" />
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <div className="h-48 bg-gray-700 rounded animate-pulse" />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="h-48 bg-gray-700 rounded animate-pulse" />
              </CardContent>
            </Card>
          </div>
        </div>
      ) : error ? (
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-500">Blad ladowania analityki</CardTitle>
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
      ) : data ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-green-500/10 p-2">
                    <DollarSign className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Calkowity przychod</p>
                    <p className="text-2xl font-bold text-green-500">
                      ${formatNumber(data.total_revenue)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-blue-500/10 p-2">
                    <ShoppingCart className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Zamowienia</p>
                    <p className="text-2xl font-bold text-blue-500">
                      {formatNumber(data.total_orders)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-teal-500/10 p-2">
                    <TrendingUp className="h-5 w-5 text-teal-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Konwersja</p>
                    <p className="text-2xl font-bold text-teal-500">
                      {data.conversion_rate}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-orange-500/10 p-2">
                    <BarChart3 className="h-5 w-5 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Srednia wartosc zamowienia</p>
                    <p className="text-2xl font-bold text-orange-500">
                      ${data.avg_order_value.toFixed(2)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Revenue by Marketplace - Horizontal Bars */}
            <Card>
              <CardHeader>
                <CardTitle className="text-white">Przychod wg marketplace&apos;u</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.revenue_by_marketplace.map((mp) => {
                    // WHY: Bar width as percentage of the highest-revenue marketplace
                    const maxRevenue = Math.max(
                      ...data.revenue_by_marketplace.map((m) => m.revenue)
                    )
                    const widthPercent = maxRevenue > 0
                      ? (mp.revenue / maxRevenue) * 100
                      : 0

                    return (
                      <div key={mp.marketplace}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-300">{mp.marketplace}</span>
                          <span className="text-sm text-white font-mono">
                            ${formatNumber(mp.revenue)} ({mp.percentage}%)
                          </span>
                        </div>
                        <div className="h-6 w-full rounded bg-gray-800">
                          <div
                            className={cn(
                              'h-6 rounded transition-all duration-500',
                              MARKETPLACE_COLORS[mp.marketplace] || 'bg-gray-500'
                            )}
                            style={{ width: `${widthPercent}%` }}
                            title={`${mp.marketplace}: $${formatNumber(mp.revenue)} (${mp.orders} orders)`}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Monthly Revenue Trend - Vertical Bars */}
            <Card>
              <CardHeader>
                <CardTitle className="text-white">Trend przychodow miesiecznych</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-3 h-48">
                  {data.monthly_revenue.map((m) => {
                    const maxRevenue = Math.max(
                      ...data.monthly_revenue.map((mo) => mo.revenue)
                    )
                    // WHY: Height as percentage of max month, min 4% so tiny bars are still visible
                    const heightPercent = maxRevenue > 0
                      ? Math.max((m.revenue / maxRevenue) * 100, 4)
                      : 4

                    return (
                      <div
                        key={m.month}
                        className="flex-1 flex flex-col items-center justify-end h-full"
                      >
                        <div
                          className="w-full rounded-t bg-teal-500 transition-all duration-500 hover:bg-teal-400"
                          style={{ height: `${heightPercent}%` }}
                          title={`${m.month}: $${formatNumber(m.revenue)} (${m.orders} orders)`}
                        />
                        <p className="text-xs text-gray-400 mt-2 whitespace-nowrap">
                          {m.month.split(' ')[0]}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Products Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-white">Najlepsze produkty wg przychodu</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Produkt</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Marketplace</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Przychod</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Sprzedane</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Konwersja</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {data.top_products.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-800/50 transition-colors">
                        <td className="px-6 py-4 text-sm text-gray-300" title={product.title}>
                          {truncate(product.title, 45)}
                        </td>
                        <td className="px-6 py-4">
                          <Badge variant="secondary">{product.marketplace}</Badge>
                        </td>
                        <td className="px-6 py-4 text-sm font-mono text-white">
                          ${formatNumber(product.revenue)}
                        </td>
                        <td className="px-6 py-4 text-sm font-mono text-gray-300">
                          {formatNumber(product.units_sold)}
                        </td>
                        <td className={cn(
                          'px-6 py-4 text-sm font-mono',
                          getConversionColor(product.conversion_rate)
                        )}>
                          {product.conversion_rate}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      ) : null}

      <FaqSection
        title="Najczesciej zadawane pytania"
        subtitle="Analityka i raporty"
        items={ANALYTICS_FAQ}
      />
    </div>
  )
}
