// frontend/src/app/listings/page.tsx
// Purpose: Compliance-focused listings page with filters and summary cards
// NOT for: Product editing or optimization (those are separate pages)

'use client'

import { useState } from 'react'
import { useListings } from '@/lib/hooks/useListings'
import { GetListingsParams } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge, ComplianceBadge } from '@/components/ui/badge'
import { formatRelativeTime, cn } from '@/lib/utils'
import { RefreshCw, ShieldCheck, AlertTriangle, XOctagon, List } from 'lucide-react'

const MARKETPLACES = ['Amazon', 'eBay', 'Walmart', 'Shopify', 'Allegro']
const COMPLIANCE_STATUSES = ['compliant', 'warning', 'suppressed', 'blocked'] as const

export default function ListingsPage() {
  const [params, setParams] = useState<GetListingsParams>({})
  const { data, isLoading, error, refetch } = useListings(params)

  const handleMarketplaceFilter = (marketplace: string) => {
    setParams((prev) => ({
      ...prev,
      marketplace: marketplace === 'all' ? undefined : marketplace,
    }))
  }

  const handleStatusFilter = (status: string) => {
    setParams((prev) => ({
      ...prev,
      compliance_status: status === 'all' ? undefined : status as GetListingsParams['compliance_status'],
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Listingi</h1>
          <p className="text-gray-400 mt-2">
            Monitoruj zgodnosc listingow na wszystkich marketplace&apos;ach. Sprawdz ktore oferty wymagaja poprawek.
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
                <List className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Wszystkie listingi</p>
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
                <ShieldCheck className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Zgodne</p>
                <p className="text-2xl font-bold text-green-500">
                  {data?.compliant_count ?? '—'}
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
                <p className="text-sm text-gray-400">Ostrzezenia</p>
                <p className="text-2xl font-bold text-yellow-500">
                  {data?.warning_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-500/10 p-2">
                <XOctagon className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Wstrzymane / Zablokowane</p>
                <p className="text-2xl font-bold text-red-500">
                  {data ? data.suppressed_count + data.blocked_count : '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            {/* Marketplace Filter */}
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

            {/* Compliance Status Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400 whitespace-nowrap">Status:</span>
              <div className="flex gap-2 overflow-x-auto">
                <Button
                  variant={!params.compliance_status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleStatusFilter('all')}
                >
                  Wszystkie
                </Button>
                {COMPLIANCE_STATUSES.map((s) => (
                  <Button
                    key={s}
                    variant={params.compliance_status === s ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleStatusFilter(s)}
                    className="capitalize"
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Listings Table */}
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
            <CardTitle className="text-red-500">Blad ladowania listingow</CardTitle>
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
      ) : data && data.listings.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">SKU</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Tytul</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Marketplace</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Zgodnosc</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Problemy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Ostatnie sprawdzenie</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.listings.map((listing) => (
                    <tr key={listing.sku} className="hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-mono text-white">
                        {listing.sku}
                      </td>
                      <td className="px-6 py-4 text-sm text-white max-w-xs truncate">
                        {listing.title}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="secondary">{listing.marketplace}</Badge>
                      </td>
                      <td className="px-6 py-4">
                        <ComplianceBadge status={listing.compliance_status} />
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={cn(
                          listing.issues_count === 0 && 'text-gray-500',
                          listing.issues_count > 0 && listing.issues_count <= 2 && 'text-yellow-500',
                          listing.issues_count > 2 && 'text-red-500',
                        )}>
                          {listing.issues_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400">
                        {formatRelativeTime(listing.last_checked)}
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
            <p className="text-gray-400">Brak listingow pasujacych do wybranych filtrow</p>
            <Button
              className="mt-4"
              variant="outline"
              onClick={() => setParams({})}
            >
              Wyczysc filtry
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
