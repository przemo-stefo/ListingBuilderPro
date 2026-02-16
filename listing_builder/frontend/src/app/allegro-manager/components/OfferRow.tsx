// frontend/src/app/allegro-manager/components/OfferRow.tsx
// Purpose: Single table row for an Allegro offer with checkbox and expand/collapse
// NOT for: Bulk actions or table orchestration (that's in OffersTable.tsx)

'use client'

import { memo } from 'react'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AllegroOffer } from '@/lib/types'
import OfferEditPanel from './OfferEditPanel'

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-green-500/20 text-green-400',
  INACTIVE: 'bg-yellow-500/20 text-yellow-400',
  ENDED: 'bg-gray-500/20 text-gray-400',
}

interface OfferRowProps {
  offer: AllegroOffer
  isSelected: boolean
  isExpanded: boolean
  onToggleSelect: (id: string) => void
  onToggleExpand: (id: string) => void
}

export const OfferRow = memo(function OfferRow({
  offer,
  isSelected,
  isExpanded,
  onToggleSelect,
  onToggleExpand,
}: OfferRowProps) {
  return (
    <>
      <tr
        className={cn(
          'border-b border-gray-800/50 hover:bg-white/5 cursor-pointer transition-colors',
          isExpanded && 'bg-white/5'
        )}
      >
        <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => onToggleSelect(offer.id)}
            role="checkbox"
            aria-checked={isSelected}
            aria-label={`Zaznacz ofertę: ${offer.name}`}
            className="flex items-center justify-center"
          >
            <div className={cn(
              'h-4 w-4 rounded border flex items-center justify-center',
              isSelected ? 'border-white bg-white' : 'border-gray-600'
            )}>
              {isSelected && <Check className="h-3 w-3 text-black" />}
            </div>
          </button>
        </td>
        <td className="px-2 py-2" onClick={() => onToggleExpand(offer.id)}>
          {offer.image ? (
            <img
              src={offer.image}
              alt=""
              className="h-8 w-8 rounded object-cover bg-gray-800"
            />
          ) : (
            <div className="h-8 w-8 rounded bg-gray-800" />
          )}
        </td>
        <td
          className="px-3 py-2 text-white truncate max-w-xs"
          onClick={() => onToggleExpand(offer.id)}
        >
          {offer.name}
        </td>
        <td
          className="px-3 py-2 text-right text-gray-300 font-mono"
          onClick={() => onToggleExpand(offer.id)}
        >
          {offer.price.amount} {offer.price.currency}
        </td>
        <td
          className="px-3 py-2 text-right text-gray-400"
          onClick={() => onToggleExpand(offer.id)}
        >
          {offer.stock.available}
        </td>
        <td
          className="px-3 py-2 text-center"
          onClick={() => onToggleExpand(offer.id)}
        >
          <span className={cn(
            'inline-block rounded-full px-2 py-0.5 text-xs font-medium',
            STATUS_COLORS[offer.status] ?? 'bg-gray-500/20 text-gray-400'
          )}>
            {offer.status}
          </span>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={6} className="bg-[#121212] p-0">
            <OfferEditPanel offerId={offer.id} />
          </td>
        </tr>
      )}
    </>
  )
})
