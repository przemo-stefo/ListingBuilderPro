// src/app/dashboard/buy-box/page.tsx
// Purpose: Buy Box monitoring page with win/loss tracking and price comparison
// NOT for: Buy box repricing logic or API definitions (see /lib/api.ts)

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getBuyBox } from '@/lib/api';
import type { BuyBoxStatus } from '@/types';
import {
  ShoppingCart,
  Trophy,
  TrendingDown,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { cn, formatCurrency, formatPercent, formatRelativeTime } from '@/lib/utils';

export default function BuyBoxPage() {
  const [items, setItems] = useState<BuyBoxStatus[]>([]);
  const [winCount, setWinCount] = useState(0);
  const [loseCount, setLoseCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lostOnly, setLostOnly] = useState(false);

  useEffect(() => {
    fetchBuyBox();
  }, [lostOnly]);

  async function fetchBuyBox() {
    setLoading(true);
    setError(null);

    try {
      const params = lostOnly ? { lost_only: true } : {};
      const data = await getBuyBox(params);
      setItems(data.items);
      setWinCount(data.winning_count);
      setLoseCount(data.losing_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load buy box data');
    } finally {
      setLoading(false);
    }
  }

  const total = winCount + loseCount;
  const winRate = total > 0 ? (winCount / total) * 100 : 0;

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
            onClick={fetchBuyBox}
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
          <h1 className="text-2xl font-bold text-white">Buy Box</h1>
          <p className="text-muted-foreground">
            Track Buy Box ownership and competitor pricing across your ASINs
          </p>
        </div>
        <button
          onClick={fetchBuyBox}
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
              <ShoppingCart className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{total}</p>
              <p className="text-xs text-muted-foreground">Total ASINs</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-green-500/10 p-2">
              <Trophy className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-500">{winCount}</p>
              <p className="text-xs text-muted-foreground">Winning</p>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(loseCount > 0 && 'border-red-500/30')}>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-red-500/10 p-2">
              <TrendingDown className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-500">{loseCount}</p>
              <p className="text-xs text-muted-foreground">Losing</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-yellow-500/10 p-2">
              <BarChart3 className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className={cn(
                'text-2xl font-bold',
                winRate >= 80 ? 'text-green-500' :
                winRate >= 50 ? 'text-yellow-500' : 'text-red-500'
              )}>
                {formatPercent(winRate)}
              </p>
              <p className="text-xs text-muted-foreground">Win Rate</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="lost-only-toggle"
            checked={lostOnly}
            onChange={e => setLostOnly(e.target.checked)}
            className="h-4 w-4 rounded border-border bg-card accent-green-500"
          />
          <label htmlFor="lost-only-toggle" className="text-sm text-muted-foreground cursor-pointer">
            Lost Buy Box Only
          </label>
        </div>
      </div>

      {/* Buy Box Table */}
      {items.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <CheckCircle className="mb-2 h-8 w-8 text-green-500" />
            <p>No ASINs found</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">ASIN</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">SKU</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Title</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Your Price</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Buy Box Price</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Difference</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Checked</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr
                  key={item.asin}
                  className={cn(
                    'border-b border-border last:border-0 hover:bg-muted/50 transition-colors',
                    !item.has_buy_box && 'bg-red-500/5'
                  )}
                >
                  <td className="px-4 py-3">
                    {item.has_buy_box ? (
                      <Badge variant="success">Won</Badge>
                    ) : (
                      <Badge variant="danger">Lost</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-white">{item.asin}</td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{item.sku || '—'}</td>
                  <td className="px-4 py-3 text-white max-w-[220px] truncate">{item.title || '—'}</td>
                  <td className="px-4 py-3 text-right text-white">{formatCurrency(item.your_price)}</td>
                  <td className="px-4 py-3 text-right text-white">{formatCurrency(item.buy_box_price)}</td>
                  <td className={cn(
                    'px-4 py-3 text-right font-medium',
                    item.price_difference && item.price_difference > 0 ? 'text-red-500' : 'text-green-500',
                  )}>
                    {item.price_difference && item.price_difference > 0
                      ? `+${formatCurrency(item.price_difference)}`
                      : '—'
                    }
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {formatRelativeTime(item.last_checked)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
