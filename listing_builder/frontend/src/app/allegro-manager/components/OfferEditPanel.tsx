// frontend/src/app/allegro-manager/components/OfferEditPanel.tsx
// Purpose: Inline edit panel for a single Allegro offer — title, price, description
// NOT for: Bulk operations (those are in OffersTable.tsx)

'use client'

import { useState, useEffect } from 'react'
import { Save, Sparkles, Loader2, ExternalLink } from 'lucide-react'
import { useOfferDetail, useUpdateOffer } from '@/lib/hooks/useAllegroOffers'

export default function OfferEditPanel({ offerId }: { offerId: string }) {
  const { data: detail, isLoading, error } = useOfferDetail(offerId)
  const updateMutation = useUpdateOffer()

  const [title, setTitle] = useState('')
  const [price, setPrice] = useState('')
  const [currency, setCurrency] = useState('PLN')
  const [dirty, setDirty] = useState(false)

  // WHY: Populate form when detail loads, or re-populate after successful save (dirty resets to false)
  useEffect(() => {
    if (detail && !dirty) {
      setTitle(detail.title)
      setPrice(detail.price)
      setCurrency(detail.currency)
    }
  }, [detail, dirty])

  const handleSave = () => {
    const data: Record<string, unknown> = {}
    if (title !== detail?.title) data.name = title
    if (price !== detail?.price || currency !== detail?.currency) {
      data.price = { amount: price, currency }
    }
    if (Object.keys(data).length === 0) return

    updateMutation.mutate(
      { offerId, data },
      { onSuccess: () => setDirty(false) }
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
      </div>
    )
  }

  if (error || !detail) {
    return (
      <div className="px-6 py-4 text-sm text-red-400">
        {(error as Error)?.message || 'Nie udało się pobrać szczegółów'}
      </div>
    )
  }

  return (
    <div className="px-6 py-4 space-y-4">
      <div className="flex items-start gap-6">
        {/* Left — images */}
        <div className="flex-shrink-0 space-y-2">
          {detail.images.slice(0, 3).map((url, i) => (
            <img
              key={i}
              src={url}
              alt=""
              className="h-16 w-16 rounded object-cover bg-gray-800"
            />
          ))}
          {detail.images.length === 0 && (
            <div className="h-16 w-16 rounded bg-gray-800 flex items-center justify-center text-xs text-gray-600">
              Brak
            </div>
          )}
        </div>

        {/* Right — editable fields */}
        <div className="flex-1 space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Tytuł ({title.length}/75)
            </label>
            <input
              type="text"
              maxLength={75}
              value={title}
              onChange={(e) => { setTitle(e.target.value); setDirty(true) }}
              className="w-full rounded-md border border-gray-700 bg-[#1A1A1A] px-3 py-1.5 text-sm text-white focus:border-gray-500 focus:outline-none"
            />
          </div>

          <div className="flex gap-3">
            <div className="w-40">
              <label className="block text-xs text-gray-500 mb-1">Cena</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={price}
                onChange={(e) => { setPrice(e.target.value); setDirty(true) }}
                className="w-full rounded-md border border-gray-700 bg-[#1A1A1A] px-3 py-1.5 text-sm text-white focus:border-gray-500 focus:outline-none"
              />
            </div>
            <div className="w-20">
              <label className="block text-xs text-gray-500 mb-1">Waluta</label>
              <div className="rounded-md border border-gray-800 bg-[#121212] px-3 py-1.5 text-sm text-gray-500">
                {currency}
              </div>
            </div>
          </div>

          {/* Meta info */}
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
            {detail.ean && <span>EAN: {detail.ean}</span>}
            {detail.brand && <span>Marka: {detail.brand}</span>}
            {detail.condition && <span>Stan: {detail.condition}</span>}
            <span>Ilość: {detail.quantity}</span>
            {detail.category && <span>Kategoria: {detail.category}</span>}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={handleSave}
              disabled={!dirty || updateMutation.isPending}
              className="flex items-center gap-1.5 rounded-md bg-white px-4 py-1.5 text-xs font-medium text-black hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Save className="h-3 w-3" />
              )}
              Zapisz
            </button>
            <a
              href={`/optimize?prefill=${encodeURIComponent(detail.title)}`}
              className="flex items-center gap-1.5 rounded-md border border-gray-700 px-4 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
            >
              <Sparkles className="h-3 w-3" />
              Optymalizuj z AI
            </a>
            <a
              href={detail.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-md border border-gray-700 px-4 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:border-gray-500 transition-colors ml-auto"
            >
              <ExternalLink className="h-3 w-3" />
              Zobacz na Allegro
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
