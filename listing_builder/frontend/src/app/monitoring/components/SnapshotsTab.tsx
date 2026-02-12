// frontend/src/app/monitoring/components/SnapshotsTab.tsx
// Purpose: Snapshot history — price/stock charts for a selected tracked product
// NOT for: Product tracking CRUD or alert management

'use client'

import { useState, useMemo } from 'react'
import { useTrackedProducts, useSnapshots } from '@/lib/hooks/useMonitoring'
import { BarChart3 } from 'lucide-react'

export default function SnapshotsTab() {
  const { data: tracked } = useTrackedProducts()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data: snapData, isLoading } = useSnapshots(selectedId, 100)

  // WHY reverse: API returns newest first, but chart needs oldest → newest
  const snapshots = useMemo(
    () => [...(snapData?.items || [])].reverse(),
    [snapData]
  )

  const prices = snapshots
    .map((s) => s.snapshot_data?.price as number | null)
    .filter((p): p is number => p != null)

  const stocks = snapshots
    .map((s) => s.snapshot_data?.stock as number | null)
    .filter((s): s is number => s != null)

  const maxPrice = prices.length ? Math.max(...prices) : 0
  const currentSnap = snapshots.length ? snapshots[snapshots.length - 1] : null

  return (
    <div className="space-y-6">
      {/* Product selector */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
        <p className="mb-3 text-sm font-medium text-white">Select Product</p>
        <select
          value={selectedId || ''}
          onChange={(e) => setSelectedId(e.target.value || null)}
          className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
        >
          <option value="">Choose a tracked product...</option>
          {tracked?.items.map((p) => (
            <option key={p.id} value={p.id}>
              [{p.marketplace}] {p.product_title || p.product_id}
            </option>
          ))}
        </select>
      </div>

      {/* No selection state */}
      {!selectedId && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          Select a product above to view snapshot history.
        </div>
      )}

      {/* Loading */}
      {selectedId && isLoading && (
        <div className="h-48 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
      )}

      {/* Stats row */}
      {selectedId && !isLoading && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Total Snapshots" value={snapData?.total ?? 0} />
          <StatCard
            label="Current Price"
            value={
              currentSnap?.snapshot_data?.price != null
                ? `$${(currentSnap.snapshot_data.price as number).toFixed(2)}`
                : '—'
            }
          />
          <StatCard
            label="Current Stock"
            value={currentSnap?.snapshot_data?.stock != null ? String(currentSnap.snapshot_data.stock) : '—'}
          />
          <StatCard
            label="Status"
            value={currentSnap?.snapshot_data?.listing_active ? 'Active' : 'Ended'}
            color={currentSnap?.snapshot_data?.listing_active ? 'text-green-400' : 'text-red-400'}
          />
        </div>
      )}

      {/* Price chart */}
      {selectedId && !isLoading && prices.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          <p className="mb-4 text-sm font-medium text-white flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-gray-400" />
            Price History
          </p>
          <div className="flex items-end gap-1 h-32">
            {prices.map((price, i) => {
              const pct = maxPrice > 0 ? (price / maxPrice) * 100 : 0
              const ts = snapshots[i]?.created_at
              const label = ts ? new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 group" title={`$${price.toFixed(2)} — ${label}`}>
                  <span className="text-[10px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                    ${price.toFixed(2)}
                  </span>
                  <div
                    className="w-full rounded-t bg-green-500/70 transition-all hover:bg-green-400 min-h-[2px]"
                    style={{ height: `${Math.max(pct, 2)}%` }}
                  />
                </div>
              )
            })}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-gray-600">
            <span>{snapshots[0]?.created_at ? new Date(snapshots[0].created_at).toLocaleDateString() : ''}</span>
            <span>{currentSnap?.created_at ? new Date(currentSnap.created_at).toLocaleDateString() : ''}</span>
          </div>
        </div>
      )}

      {/* Stock history */}
      {selectedId && !isLoading && stocks.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
          <p className="mb-4 text-sm font-medium text-white">Stock History</p>
          <div className="space-y-1">
            {snapshots.slice(-10).map((snap, i) => {
              const stock = snap.snapshot_data?.stock as number | null
              if (stock == null) return null
              const date = new Date(snap.created_at).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
              })
              return (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">{date}</span>
                  <span className={stock < 5 ? 'text-red-400 font-medium' : 'text-gray-300'}>
                    {stock} units
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* No snapshots yet */}
      {selectedId && !isLoading && !snapshots.length && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          No snapshots yet for this product. Use &quot;Poll Now&quot; in the Products tab.
        </div>
      )}
    </div>
  )
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string
  value: string | number
  color?: string
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-[#121212] p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-lg font-semibold ${color || 'text-white'} mt-1`}>{value}</p>
    </div>
  )
}
