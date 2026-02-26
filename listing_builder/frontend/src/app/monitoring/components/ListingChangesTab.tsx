// frontend/src/app/monitoring/components/ListingChangesTab.tsx
// Purpose: Timeline of field-level listing changes for tracked Amazon products
// NOT for: Change detection logic (backend) or snapshot charts (SnapshotsTab)

'use client'

import { useState } from 'react'
import { useTrackedProducts, useListingChanges } from '@/lib/hooks/useMonitoring'
import { Type, List, FileText, Image, DollarSign, Tag, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ListingChange } from '@/lib/types'

const CHANGE_TYPE_CONFIG: Record<string, { label: string; icon: typeof Type; color: string }> = {
  title: { label: 'Tytuł', icon: Type, color: 'text-blue-400' },
  bullets: { label: 'Bullets', icon: List, color: 'text-green-400' },
  description: { label: 'Opis', icon: FileText, color: 'text-yellow-400' },
  images: { label: 'Zdjęcia', icon: Image, color: 'text-purple-400' },
  price: { label: 'Cena', icon: DollarSign, color: 'text-orange-400' },
  brand: { label: 'Marka', icon: Tag, color: 'text-red-400' },
}

const FILTER_OPTIONS = [
  { key: '', label: 'Wszystko' },
  { key: 'title', label: 'Tytuł' },
  { key: 'bullets', label: 'Bullets' },
  { key: 'description', label: 'Opis' },
  { key: 'images', label: 'Zdjęcia' },
  { key: 'price', label: 'Cena' },
]

const PAGE_SIZE = 20

export default function ListingChangesTab() {
  const { data: tracked } = useTrackedProducts()
  const [selectedProductId, setSelectedProductId] = useState<string>('')
  const [changeTypeFilter, setChangeTypeFilter] = useState<string>('')
  const [offset, setOffset] = useState(0)

  // WHY filter Amazon only: Listing changes come from SP-API, only Amazon has it
  const amazonProducts = tracked?.items.filter((p) => p.marketplace === 'amazon') || []

  const { data, isLoading } = useListingChanges({
    product_id: selectedProductId || undefined,
    change_type: changeTypeFilter || undefined,
    limit: PAGE_SIZE,
    offset,
  })

  const hasNext = data ? offset + PAGE_SIZE < data.total : false
  const hasPrev = offset > 0

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5 space-y-4">
        {/* Product selector */}
        <div>
          <p className="mb-2 text-sm font-medium text-white">Produkt (Amazon)</p>
          <select
            value={selectedProductId}
            onChange={(e) => { setSelectedProductId(e.target.value); setOffset(0) }}
            className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
          >
            <option value="">Wszystkie produkty</option>
            {amazonProducts.map((p) => (
              <option key={p.id} value={p.product_id}>
                {p.product_title || p.product_id}
              </option>
            ))}
          </select>
        </div>

        {/* Change type filter */}
        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => { setChangeTypeFilter(key); setOffset(0) }}
              className={cn(
                'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                changeTypeFilter === key
                  ? 'bg-white/15 text-white'
                  : 'bg-white/5 text-gray-400 hover:text-white'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="h-48 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
      )}

      {/* Empty state */}
      {!isLoading && (!data?.items.length) && (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          Brak wykrytych zmian listingów. Zmiany pojawią się po kolejnym pollingu Amazon (co 4h).
        </div>
      )}

      {/* Timeline */}
      {!isLoading && data?.items && data.items.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-gray-500">
            {data.total} zmian{data.total === 1 ? 'a' : data.total < 5 ? 'y' : ''}
          </p>

          {data.items.map((change) => (
            <ChangeCard key={change.id} change={change} />
          ))}

          {/* Pagination */}
          {(hasNext || hasPrev) && (
            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={!hasPrev}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-white disabled:opacity-30"
              >
                <ChevronLeft className="h-3 w-3" /> Nowsze
              </button>
              <span className="text-xs text-gray-600">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} z {data.total}
              </span>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={!hasNext}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-white disabled:opacity-30"
              >
                Starsze <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ChangeCard({ change }: { change: ListingChange }) {
  const config = CHANGE_TYPE_CONFIG[change.change_type] || CHANGE_TYPE_CONFIG.title
  const Icon = config.icon
  const date = new Date(change.detected_at).toLocaleString('pl-PL', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  const isImage = change.change_type === 'images'

  return (
    <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className={cn('rounded-md bg-white/5 p-1.5', config.color)}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">{config.label}</span>
            {change.field_name && (
              <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-gray-400">
                {change.field_name}
              </span>
            )}
          </div>
          <p className="text-[11px] text-gray-500">{change.product_id} &middot; {date}</p>
        </div>
      </div>

      {/* Diff content */}
      <div className="space-y-2">
        {change.old_value && (
          isImage ? (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-red-400/70 shrink-0">OLD</span>
              <img src={change.old_value} alt="old" className="h-16 w-16 rounded border border-red-900/30 object-cover" />
            </div>
          ) : (
            <div className="rounded bg-red-500/5 border border-red-900/20 px-3 py-2">
              <p className="text-xs text-red-400/80 break-words line-clamp-4">{change.old_value}</p>
            </div>
          )
        )}
        {change.new_value && (
          isImage ? (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-green-400/70 shrink-0">NEW</span>
              <img src={change.new_value} alt="new" className="h-16 w-16 rounded border border-green-900/30 object-cover" />
            </div>
          ) : (
            <div className="rounded bg-green-500/5 border border-green-900/20 px-3 py-2">
              <p className="text-xs text-green-400/80 break-words line-clamp-4">{change.new_value}</p>
            </div>
          )
        )}
      </div>
    </div>
  )
}
