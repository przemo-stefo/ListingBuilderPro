// frontend/src/app/keywords/page.tsx
// Purpose: SEO keyword tracking page with filters, summary cards, and keyword table
// NOT for: Product editing or listing compliance (those are separate pages)

'use client'

import { useState, useMemo, useCallback } from 'react'
import { useKeywords } from '@/lib/hooks/useKeywords'
import { GetKeywordsParams } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { formatRelativeTime, formatNumber, getScoreColor, cn, debounce } from '@/lib/utils'
import {
  RefreshCw,
  Hash,
  Eye,
  Trophy,
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
} from 'lucide-react'

const MARKETPLACES = ['Amazon', 'eBay', 'Walmart', 'Shopify', 'Allegro']

// WHY: Color-codes rank so users can quickly spot which keywords need attention
function getRankColor(rank: number | null): string {
  if (rank === null) return 'text-gray-500'
  if (rank <= 10) return 'text-green-500'
  if (rank <= 50) return 'text-yellow-500'
  return 'text-red-500'
}

// WHY: Visual trend indicator with color for fast scanning
function TrendIcon({ trend }: { trend: 'up' | 'down' | 'stable' }) {
  if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />
  if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-500" />
  return <Minus className="h-4 w-4 text-gray-500" />
}

export default function KeywordsPage() {
  const [params, setParams] = useState<GetKeywordsParams>({})
  const [searchInput, setSearchInput] = useState('')
  const { data, isLoading, error, refetch } = useKeywords(params)

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
          <h1 className="text-3xl font-bold text-white">Keywords</h1>
          <p className="text-gray-400 mt-2">
            Track keyword rankings and search volume across marketplaces
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
                <Hash className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Keywords</p>
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
                <Eye className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Tracked</p>
                <p className="text-2xl font-bold text-green-500">
                  {data?.tracked_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-yellow-500/10 p-2">
                <Trophy className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Top 10 Ranked</p>
                <p className="text-2xl font-bold text-yellow-500">
                  {data?.top_10_count ?? '—'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-teal-500/10 p-2">
                <Target className="h-5 w-5 text-teal-500" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Avg Relevance</p>
                <p className="text-2xl font-bold text-teal-500">
                  {data?.avg_relevance ?? '—'}
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
                placeholder="Search keywords..."
                value={searchInput}
                onChange={handleSearchChange}
                className="w-64"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Keywords Table */}
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
            <CardTitle className="text-red-500">Error Loading Keywords</CardTitle>
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
      ) : data && data.keywords.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Keyword</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Marketplace</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Search Volume</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Rank</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Trend</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Relevance</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.keywords.map((kw) => (
                    <tr key={kw.id} className="hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-white">
                        {kw.keyword}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="secondary">{kw.marketplace}</Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-white font-mono">
                        {formatNumber(kw.search_volume)}
                      </td>
                      <td className="px-6 py-4 text-sm font-mono">
                        <span className={getRankColor(kw.current_rank)}>
                          {kw.current_rank !== null ? `#${kw.current_rank}` : '—'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <TrendIcon trend={kw.trend} />
                      </td>
                      <td className="px-6 py-4 text-sm font-mono">
                        <span className={getScoreColor(kw.relevance_score)}>
                          {kw.relevance_score}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400">
                        {formatRelativeTime(kw.last_updated)}
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
            <p className="text-gray-400">No keywords match the selected filters</p>
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
