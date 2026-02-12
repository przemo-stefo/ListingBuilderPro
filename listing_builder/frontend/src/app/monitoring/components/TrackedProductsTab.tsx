// frontend/src/app/monitoring/components/TrackedProductsTab.tsx
// Purpose: Track/untrack products, show latest snapshot data, trigger manual polls
// NOT for: Snapshot history or alert rules

'use client'

import { useState } from 'react'
import {
  useTrackedProducts,
  useTrackProduct,
  useUntrackProduct,
  useToggleTracking,
  usePollMarketplace,
  useSnapshots,
} from '@/lib/hooks/useMonitoring'
import { Trash2, Power, RefreshCw, ExternalLink } from 'lucide-react'
import type { TrackedProduct } from '@/lib/types'

const MARKETPLACES = ['allegro', 'amazon', 'kaufland', 'ebay'] as const
const POLL_OPTIONS = [1, 3, 6, 12, 24]

// WHY: inline component — avoids N+1 queries by fetching latest snapshot per product
function SnapshotBadge({ product }: { product: TrackedProduct }) {
  const { data } = useSnapshots(product.id, 1)
  const snap = data?.items?.[0]?.snapshot_data

  if (!snap) return <span className="text-xs text-gray-600">No data yet</span>

  const price = snap.price as number | null
  const currency = (snap.currency as string) || ''
  const stock = snap.stock as number | null
  const active = snap.listing_active as boolean

  return (
    <div className="flex items-center gap-3 text-xs">
      {price != null && (
        <span className="text-green-400 font-medium">
          {currency === 'USD' ? '$' : currency}{price.toFixed(2)}
        </span>
      )}
      {stock != null && (
        <span className={stock < 5 ? 'text-red-400' : 'text-gray-400'}>
          {stock} in stock
        </span>
      )}
      <span className={active ? 'text-green-500' : 'text-red-500'}>
        {active ? 'Active' : 'Ended'}
      </span>
    </div>
  )
}

export default function TrackedProductsTab() {
  const { data, isLoading } = useTrackedProducts()
  const trackMutation = useTrackProduct()
  const untrackMutation = useUntrackProduct()
  const toggleMutation = useToggleTracking()
  const pollMutation = usePollMarketplace()

  const [marketplace, setMarketplace] = useState<string>('ebay')
  const [productId, setProductId] = useState('')
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [pollInterval, setPollInterval] = useState(6)

  const handleTrack = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!productId.trim()) return

    await trackMutation.mutateAsync({
      marketplace,
      product_id: productId.trim(),
      product_title: title.trim() || undefined,
      product_url: url.trim() || undefined,
      poll_interval_hours: pollInterval,
    })

    setProductId('')
    setTitle('')
    setUrl('')
  }

  // WHY: Group products by marketplace for "Poll Now" buttons
  const marketplacesWithProducts = data?.items
    ? [...new Set(data.items.map((p) => p.marketplace))]
    : []

  return (
    <div className="space-y-6">
      {/* Poll Now buttons */}
      {marketplacesWithProducts.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 mr-1">Poll Now:</span>
          {marketplacesWithProducts.map((mp) => (
            <button
              key={mp}
              onClick={() => pollMutation.mutate(mp)}
              disabled={pollMutation.isPending}
              className="flex items-center gap-1.5 rounded-md border border-gray-700 bg-[#121212] px-3 py-1.5 text-xs text-white transition-colors hover:bg-white/10 disabled:opacity-50"
            >
              <RefreshCw className={`h-3 w-3 ${pollMutation.isPending ? 'animate-spin' : ''}`} />
              {mp}
            </button>
          ))}
        </div>
      )}

      {/* Track form */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
        <p className="mb-4 text-sm font-medium text-white">Track a Product</p>
        <form onSubmit={handleTrack} className="space-y-3">
          <div className="grid grid-cols-5 gap-3">
            <select
              value={marketplace}
              onChange={(e) => setMarketplace(e.target.value)}
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
            >
              {MARKETPLACES.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>

            <input
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              placeholder="Product ID (ASIN, item ID...)"
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
              required
            />

            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title (optional)"
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
            />

            <select
              value={pollInterval}
              onChange={(e) => setPollInterval(Number(e.target.value))}
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
            >
              {POLL_OPTIONS.map((h) => (
                <option key={h} value={h}>Every {h}h</option>
              ))}
            </select>

            <button
              type="submit"
              disabled={trackMutation.isPending}
              className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-gray-200 disabled:opacity-50"
            >
              {trackMutation.isPending ? 'Tracking...' : 'Track'}
            </button>
          </div>

          {/* URL input — needed for Allegro/eBay URL-based scraping */}
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Product URL (needed for Allegro, optional for eBay)"
            className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
          />
        </form>
      </div>

      {/* Product list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
      ) : !data?.items.length ? (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          No products tracked yet. Use the form above to start monitoring.
        </div>
      ) : (
        <div className="space-y-2">
          {data.items.map((product) => (
            <div
              key={product.id}
              className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] px-5 py-3"
            >
              <div className="flex items-center gap-4 min-w-0 flex-1">
                <span className="shrink-0 rounded-full border border-gray-700 bg-white/5 px-2.5 py-0.5 text-xs text-white">
                  {product.marketplace}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-white truncate">
                    {product.product_title || product.product_id}
                  </p>
                  <div className="flex items-center gap-3 mt-0.5">
                    {product.product_title && (
                      <span className="text-xs text-gray-500">{product.product_id}</span>
                    )}
                    <SnapshotBadge product={product} />
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 ml-4">
                <span className="text-xs text-gray-500">
                  Every {product.poll_interval_hours}h
                </span>

                {product.product_url && (
                  <a
                    href={product.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-md p-1.5 text-gray-500 transition-colors hover:bg-white/10 hover:text-white"
                    title="Open listing"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}

                <button
                  onClick={() => toggleMutation.mutate(product.id)}
                  className={`rounded-md p-1.5 transition-colors ${
                    product.enabled
                      ? 'text-green-500 hover:bg-green-500/10'
                      : 'text-gray-600 hover:bg-gray-800'
                  }`}
                  title={product.enabled ? 'Disable' : 'Enable'}
                >
                  <Power className="h-4 w-4" />
                </button>

                <button
                  onClick={() => untrackMutation.mutate(product.id)}
                  className="rounded-md p-1.5 text-gray-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
                  title="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
