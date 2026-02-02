// src/app/dashboard/inventory/page.tsx
// Purpose: Inventory management page with filtering and summary cards
// NOT for: Inventory sync logic or API definitions (see /lib/api.ts)

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { MarketplaceBadge } from '@/components/ui/badge';
import { getInventory } from '@/lib/api';
import type { InventoryItem, Marketplace } from '@/types';
import {
  Package,
  Layers,
  AlertTriangle,
  XCircle,
  RefreshCw,
} from 'lucide-react';
import { cn, formatCurrency, formatNumber, formatRelativeTime } from '@/lib/utils';

type MarketplaceFilter = Marketplace | 'all';

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketplaceFilter, setMarketplaceFilter] = useState<MarketplaceFilter>('all');
  const [lowStockOnly, setLowStockOnly] = useState(false);

  useEffect(() => {
    fetchInventory();
  }, [marketplaceFilter, lowStockOnly]);

  async function fetchInventory() {
    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string | boolean> = {};
      if (marketplaceFilter !== 'all') params.marketplace = marketplaceFilter;
      if (lowStockOnly) params.low_stock = true;

      const data = await getInventory(params as Parameters<typeof getInventory>[0]);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  }

  // Summary counts from current item list
  const counts = {
    totalSkus: items.length,
    totalUnits: items.reduce((sum, i) => sum + i.quantity, 0),
    lowStock: items.filter(i => i.quantity > 0 && i.quantity <= 20).length,
    outOfStock: items.filter(i => i.quantity === 0).length,
  };

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
            onClick={fetchInventory}
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
          <h1 className="text-2xl font-bold text-white">Inventory</h1>
          <p className="text-muted-foreground">
            Track stock levels across all connected marketplaces
          </p>
        </div>
        <button
          onClick={fetchInventory}
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
              <Package className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{formatNumber(counts.totalSkus)}</p>
              <p className="text-xs text-muted-foreground">Total SKUs</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-green-500/10 p-2">
              <Layers className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{formatNumber(counts.totalUnits)}</p>
              <p className="text-xs text-muted-foreground">Total Units</p>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(counts.lowStock > 0 && 'border-yellow-500/30')}>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-yellow-500/10 p-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-500">{counts.lowStock}</p>
              <p className="text-xs text-muted-foreground">Low Stock</p>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(counts.outOfStock > 0 && 'border-red-500/30')}>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-red-500/10 p-2">
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-500">{counts.outOfStock}</p>
              <p className="text-xs text-muted-foreground">Out of Stock</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
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
        <div className="flex items-center gap-2 pt-4">
          <input
            type="checkbox"
            id="low-stock-toggle"
            checked={lowStockOnly}
            onChange={e => setLowStockOnly(e.target.checked)}
            className="h-4 w-4 rounded border-border bg-card accent-green-500"
          />
          <label htmlFor="low-stock-toggle" className="text-sm text-muted-foreground cursor-pointer">
            Low Stock Only
          </label>
        </div>
      </div>

      {/* Inventory Table */}
      {items.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Package className="mb-2 h-8 w-8 text-green-500" />
            <p>No inventory items found</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">SKU</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Title</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Marketplace</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Quantity</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Price</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Fulfillment</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">Updated</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr
                  key={item.sku}
                  className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-white">{item.sku}</td>
                  <td className="px-4 py-3 text-white max-w-[250px] truncate">{item.title}</td>
                  <td className="px-4 py-3">
                    <MarketplaceBadge marketplace={item.marketplace} />
                  </td>
                  <td className={cn(
                    'px-4 py-3 text-right font-medium',
                    item.quantity === 0 && 'text-red-500',
                    item.quantity > 0 && item.quantity <= 20 && 'text-yellow-500',
                    item.quantity > 20 && 'text-white',
                  )}>
                    {formatNumber(item.quantity)}
                  </td>
                  <td className="px-4 py-3 text-right text-white">{formatCurrency(item.price)}</td>
                  <td className="px-4 py-3 text-muted-foreground">{item.fulfillment_channel || '—'}</td>
                  <td className="px-4 py-3 text-right text-muted-foreground">{formatRelativeTime(item.last_updated)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
