// frontend/src/app/competitors/page.tsx
// Purpose: Competitor tracking page with pricing comparison, ratings, and win/lose status
// NOT for: Product editing or keyword tracking (those are separate pages)

'use client'

import { useState, useMemo, useCallback } from 'react'
import { useCompetitors } from '@/lib/hooks/useCompetitors'
import { GetCompetitorsParams, CompetitorStatus } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { formatRelativeTime, formatNumber, truncate, cn, debounce } from '@/lib/utils'
import {
  RefreshCw,
  Users,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Star,
  Search,
} from 'lucide-react'

const MARKETPLACES = ['Amazon', 'eBay', 'Walmart', 'Shopify', 'Allegro']

// WHY: Color-coded status badge so users can instantly spot competitive position
function StatusBadge({ status }: { status: CompetitorStatus }) {
  const config: Record<CompetitorStatus, { label: string; className: string }> = {
    winning: {
      label: 'Winning',
      className: 'bg-green-500/10 text-green-500 border-green-500/20',
    },
    losing: {
      label: 'Losing',
      className: 'bg-red-500/10 text-red-500 border-red-500/20',
    },
    tied: {
      label: 'Tied',
      className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    },
  }

  const c = config[status]

  return (
    <Badge className={cn('text-xs', c.className)}>
      {c.label}
    </Badge>
  )
}

// WHY: Filled star icon with rating number for quick visual scanning
function RatingDisplay({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
      <span className="text-sm text-white">{rating.toFixed(1)}</span>
    </div>
  )
}

// WHY: Green = we're cheaper (winning), red = they're cheaper (losing), gray = tied
function getPriceDiffColor(diff: number): string {
  if (diff > 0) return 'text-green-500'
  if (diff < 0) return 'text-red-500'
  return 'text-gray-500'
}

// WHY: Formats price difference with +/- prefix for clarity
function formatPriceDiff(diff: number): string {
  if (diff > 0) return `+$${diff.toFixed(2)}`
  if (diff < 0) return `-$${Math.abs(diff).toFixed(2)}`
  return '$0.00'
}

export default function CompetitorsPage() {
  const [params, setParams] = useState<GetCompetitorsParams>({})
  const [searchInput, setSearchInput] = useState('')
  const { data, isLoading, error, refetch } = useCompetitors(params)

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

  const clearFilters = () => {
    setParams({})
    setSearchInput('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Competitors</h1>
          <p className="text-gray-400 mt-2">
            Track competitor pricing, ratings, and market position across marketplaces
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={cn('mr-2 h-4 w-4', isLoading && 'animate-spin')} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <Users className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Competitors</p>
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
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Winning</p>
                <p className="text-2xl font-bold text-green-500">
                  {data?.winning_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-500/10 p-2">
                <TrendingDown className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Losing</p>
                <p className="text-2xl font-bold text-red-500">
                  {data?.losing_count ?? '—'}
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
                <p className="text-sm text-gray-400">Avg Price Gap</p>
                <p className="text-2xl font-bold text-teal-500">
                  {data?.avg_price_gap != null ? `$${data.avg_price_gap.toFixed(2)}` : '—'}
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
                  All
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

            {/* Search Filter */}
            <div className="flex items-center gap-2 md:ml-auto">
              <Search className="h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search competitors..."
                value={searchInput}
                onChange={handleSearchChange}
                className="w-64"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Competitors Table */}
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
            <CardTitle className="text-red-500">Error Loading Competitors</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-400 mb-4">
              {error instanceof Error ? error.message : 'Something went wrong'}
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : data && data.competitors.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Competitor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Product</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Marketplace</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Their Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Our Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Diff</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rating</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Reviews</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Last Checked</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.competitors.map((comp) => (
                    <tr key={comp.id} className="hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-white">
                        {comp.competitor_name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300" title={comp.product_title}>
                        {truncate(comp.product_title, 40)}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="secondary">{comp.marketplace}</Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        ${comp.their_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        ${comp.our_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm font-mono">
                        <span className={getPriceDiffColor(comp.price_difference)}>
                          {formatPriceDiff(comp.price_difference)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <RatingDisplay rating={comp.their_rating} />
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        {formatNumber(comp.their_reviews_count)}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={comp.status} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400">
                        {formatRelativeTime(comp.last_checked)}
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
            <p className="text-gray-400">No competitors match the selected filters</p>
            <Button
              className="mt-4"
              variant="outline"
              onClick={clearFilters}
            >
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
