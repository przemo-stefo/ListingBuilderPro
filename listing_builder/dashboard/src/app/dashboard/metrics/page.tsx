// src/app/dashboard/metrics/page.tsx
// Purpose: Seller performance metrics page with per-marketplace breakdown
// NOT for: Metrics calculation or API definitions (see /lib/api.ts)

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MarketplaceBadge } from '@/components/ui/badge';
import { getMetrics } from '@/lib/api';
import type { SellerMetrics, Marketplace } from '@/types';
import {
  BarChart3,
  DollarSign,
  ShoppingBag,
  RefreshCw,
  AlertTriangle,
  Star,
  RotateCcw,
  TrendingDown,
  XCircle,
  Clock,
} from 'lucide-react';
import { cn, formatCurrency, formatNumber, formatPercent, formatRelativeTime } from '@/lib/utils';

type MarketplaceFilter = Marketplace | 'all';

// Color-code rates — green when low (good), red when high (bad)
function getRateColor(rate: number, warnAt: number, dangerAt: number): string {
  if (rate >= dangerAt) return 'text-red-500';
  if (rate >= warnAt) return 'text-yellow-500';
  return 'text-green-500';
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<SellerMetrics[]>([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [totalRevenue, setTotalRevenue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketplaceFilter, setMarketplaceFilter] = useState<MarketplaceFilter>('all');

  useEffect(() => {
    fetchMetrics();
  }, [marketplaceFilter]);

  async function fetchMetrics() {
    setLoading(true);
    setError(null);

    try {
      const params = marketplaceFilter !== 'all' ? { marketplace: marketplaceFilter } : {};
      const data = await getMetrics(params as Parameters<typeof getMetrics>[0]);
      setMetrics(data.metrics);
      setTotalOrders(data.total_orders_30d);
      setTotalRevenue(data.total_revenue_30d);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-500/30 bg-red-500/5">
        <div className="flex flex-col items-center justify-center py-8">
          <AlertTriangle className="mb-2 h-8 w-8 text-red-500" />
          <p className="text-red-500">{error}</p>
          <button
            onClick={fetchMetrics}
            className="mt-4 rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-500 hover:bg-red-500/20"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Metrics</h1>
          <p className="text-muted-foreground">
            Seller performance and account health across marketplaces
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm hover:bg-muted transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-blue-500/10 p-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{metrics.length}</p>
              <p className="text-xs text-muted-foreground">Marketplaces</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-green-500/10 p-2">
              <ShoppingBag className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{formatNumber(totalOrders)}</p>
              <p className="text-xs text-muted-foreground">Orders (30d)</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-yellow-500/10 p-2">
              <DollarSign className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{formatCurrency(totalRevenue)}</p>
              <p className="text-xs text-muted-foreground">Revenue (30d)</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-orange-500/10 p-2">
              <Star className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {metrics.length > 0
                  ? (metrics.reduce((sum, m) => sum + (m.feedback_score || 0), 0) / metrics.length).toFixed(1)
                  : '—'
                }
              </p>
              <p className="text-xs text-muted-foreground">Avg Feedback</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Marketplace</label>
          <select
            value={marketplaceFilter}
            onChange={e => setMarketplaceFilter(e.target.value as MarketplaceFilter)}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500"
          >
            <option value="all">All Marketplaces</option>
            <option value="amazon">Amazon</option>
            <option value="ebay">eBay</option>
            <option value="kaufland">Kaufland</option>
            <option value="allegro">Allegro</option>
            <option value="temu">Temu</option>
          </select>
        </div>
      </div>

      {/* Per-Marketplace Cards */}
      {metrics.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <BarChart3 className="mb-2 h-8 w-8 text-green-500" />
            <p>No metrics available</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {metrics.map(m => (
            <Card key={m.marketplace}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  <MarketplaceBadge marketplace={m.marketplace} />
                  <CardTitle className="capitalize">{m.marketplace}</CardTitle>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(m.last_updated)}
                </span>
              </CardHeader>
              <CardContent>
                {/* Top row: revenue + orders */}
                <div className="mb-4 grid grid-cols-2 gap-4">
                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <DollarSign className="h-3.5 w-3.5" />
                      Revenue (30d)
                    </div>
                    <p className="mt-1 text-lg font-bold text-white">
                      {formatCurrency(m.revenue_30d)}
                    </p>
                  </div>
                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <ShoppingBag className="h-3.5 w-3.5" />
                      Orders (30d)
                    </div>
                    <p className="mt-1 text-lg font-bold text-white">
                      {formatNumber(m.order_count_30d)}
                    </p>
                  </div>
                </div>

                {/* Ratings row */}
                <div className="mb-4 grid grid-cols-2 gap-4">
                  {m.feedback_score != null && (
                    <div className="flex items-center justify-between rounded-lg border border-border p-3">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Star className="h-3.5 w-3.5" />
                        Feedback
                      </div>
                      <span className="font-bold text-white">{m.feedback_score.toFixed(1)}</span>
                    </div>
                  )}
                  {m.seller_rating != null && (
                    <div className="flex items-center justify-between rounded-lg border border-border p-3">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <BarChart3 className="h-3.5 w-3.5" />
                        Seller Rating
                      </div>
                      <span className={cn(
                        'font-bold',
                        m.seller_rating >= 98 ? 'text-green-500' :
                        m.seller_rating >= 95 ? 'text-yellow-500' : 'text-red-500'
                      )}>
                        {formatPercent(m.seller_rating)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Health metrics — lower is better */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-lg border border-border p-2 text-center">
                    <RotateCcw className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                    <p className={cn('text-sm font-bold', getRateColor(m.return_rate, 3, 5))}>
                      {formatPercent(m.return_rate)}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Returns</p>
                  </div>
                  <div className="rounded-lg border border-border p-2 text-center">
                    <XCircle className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                    <p className={cn('text-sm font-bold', getRateColor(m.defect_rate, 0.5, 1))}>
                      {formatPercent(m.defect_rate)}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Defects</p>
                  </div>
                  {m.late_shipment_rate != null && (
                    <div className="rounded-lg border border-border p-2 text-center">
                      <Clock className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                      <p className={cn('text-sm font-bold', getRateColor(m.late_shipment_rate, 1.5, 3))}>
                        {formatPercent(m.late_shipment_rate)}
                      </p>
                      <p className="text-[10px] text-muted-foreground">Late Ship</p>
                    </div>
                  )}
                  {m.cancellation_rate != null && (
                    <div className="rounded-lg border border-border p-2 text-center">
                      <TrendingDown className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                      <p className={cn('text-sm font-bold', getRateColor(m.cancellation_rate, 1, 2))}>
                        {formatPercent(m.cancellation_rate)}
                      </p>
                      <p className="text-[10px] text-muted-foreground">Cancellations</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
