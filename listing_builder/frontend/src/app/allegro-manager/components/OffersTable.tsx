// frontend/src/app/allegro-manager/components/OffersTable.tsx
// Purpose: Offers table with search, filters, bulk actions, pagination
// NOT for: Single offer edit logic (OfferEditPanel) or row rendering (OfferRow)

'use client'

import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import {
  Search, ChevronLeft, ChevronRight, Check, Play, Square, DollarSign, Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useOffersList, useBulkStatus, useBulkPrice } from '@/lib/hooks/useAllegroOffers'
import { OfferRow } from './OfferRow'

const PAGE_SIZE = 20

const STATUS_OPTIONS = [
  { value: '', label: 'Wszystkie' },
  { value: 'ACTIVE', label: 'Aktywne' },
  { value: 'INACTIVE', label: 'Nieaktywne' },
  { value: 'ENDED', label: 'Zakończone' },
]

export default function OffersTable() {
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [bulkPriceOpen, setBulkPriceOpen] = useState(false)
  const [bulkPrice, setBulkPrice] = useState('')

  // WHY useRef: previous debounce leaked timers — returned cleanup was never called
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const handleSearch = useCallback((val: string) => {
    setSearch(val)
    setPage(0)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedSearch(val), 400)
  }, [])

  // WHY: Clean up timer on unmount
  useEffect(() => () => clearTimeout(debounceRef.current), [])

  // WHY: Clear selection when page or filter changes — avoids hidden selected items
  useEffect(() => {
    setSelected(new Set())
  }, [page, statusFilter, debouncedSearch])

  const params = useMemo(() => ({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    status: statusFilter || undefined,
    search: debouncedSearch || undefined,
  }), [page, statusFilter, debouncedSearch])

  const { data, isLoading, error } = useOffersList(params)
  const bulkStatus = useBulkStatus()
  const bulkPriceMut = useBulkPrice()

  const offers = data?.offers ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const allOnPageSelected = useMemo(
    () => offers.length > 0 && offers.every((o) => selected.has(o.id)),
    [offers, selected]
  )

  const toggleAll = useCallback(() => {
    if (allOnPageSelected) {
      setSelected(new Set())
    } else {
      setSelected(new Set(offers.map((o) => o.id)))
    }
  }, [allOnPageSelected, offers])

  // WHY useCallback: stable reference for memoized OfferRow
  const toggleOne = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => prev === id ? null : id)
  }, [])

  const handleBulkStatus = (action: 'ACTIVATE' | 'END') => {
    if (selected.size === 0) return

    // WHY: Ending offers is destructive — require user confirmation
    if (action === 'END') {
      const confirmed = window.confirm(
        `Czy na pewno chcesz zakończyć ${selected.size} ofert? Ta operacja wyłączy je na Allegro.`
      )
      if (!confirmed) return
    }

    bulkStatus.mutate({ offerIds: Array.from(selected), action }, {
      onSuccess: () => setSelected(new Set()),
    })
  }

  const handleBulkPrice = () => {
    if (selected.size === 0 || !bulkPrice) return
    const changes = Array.from(selected).map((id) => ({
      offer_id: id,
      price: bulkPrice,
      currency: 'PLN',
    }))
    bulkPriceMut.mutate(changes, {
      onSuccess: () => {
        setSelected(new Set())
        setBulkPriceOpen(false)
        setBulkPrice('')
      },
    })
  }

  const isBusy = bulkStatus.isPending || bulkPriceMut.isPending

  return (
    <div className="space-y-4">
      {/* Search + filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Szukaj po tytule..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] py-2 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:border-gray-600 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0) }}
          className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-2 text-sm text-white focus:border-gray-600 focus:outline-none"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <span className="text-xs text-gray-500">{total} ofert</span>
      </div>

      {/* Bulk actions bar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-gray-700 bg-[#1A1A1A] px-4 py-2">
          <span className="text-sm text-gray-300">
            Zaznaczono: <strong className="text-white">{selected.size}</strong>
          </span>
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => handleBulkStatus('ACTIVATE')}
              disabled={isBusy}
              className="flex items-center gap-1.5 rounded-md bg-green-600/20 px-3 py-1.5 text-xs font-medium text-green-400 hover:bg-green-600/30 disabled:opacity-50"
            >
              {bulkStatus.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
              Aktywuj
            </button>
            <button
              onClick={() => handleBulkStatus('END')}
              disabled={isBusy}
              className="flex items-center gap-1.5 rounded-md bg-red-600/20 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-600/30 disabled:opacity-50"
            >
              {bulkStatus.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Square className="h-3 w-3" />}
              Zakończ
            </button>
            {bulkPriceOpen ? (
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="999999"
                  placeholder="Nowa cena"
                  value={bulkPrice}
                  onChange={(e) => setBulkPrice(e.target.value)}
                  className="w-28 rounded-md border border-gray-700 bg-[#121212] px-2 py-1.5 text-xs text-white"
                />
                <button
                  onClick={handleBulkPrice}
                  disabled={!bulkPrice || isBusy}
                  className="rounded-md bg-blue-600/20 px-3 py-1.5 text-xs font-medium text-blue-400 hover:bg-blue-600/30 disabled:opacity-50"
                >
                  {bulkPriceMut.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Zastosuj'}
                </button>
                <button
                  onClick={() => { setBulkPriceOpen(false); setBulkPrice('') }}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  Anuluj
                </button>
              </div>
            ) : (
              <button
                onClick={() => setBulkPriceOpen(true)}
                disabled={isBusy}
                className="flex items-center gap-1.5 rounded-md bg-blue-600/20 px-3 py-1.5 text-xs font-medium text-blue-400 hover:bg-blue-600/30 disabled:opacity-50"
              >
                <DollarSign className="h-3 w-3" /> Zmień cenę
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading / error states */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-400">
          {(error as Error).message}
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && (
        <div className="rounded-lg border border-gray-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-[#121212]">
                <th className="w-10 px-3 py-2">
                  <button
                    onClick={toggleAll}
                    role="checkbox"
                    aria-checked={allOnPageSelected}
                    aria-label="Zaznacz wszystkie oferty na stronie"
                    className="flex items-center justify-center"
                  >
                    <div className={cn(
                      'h-4 w-4 rounded border flex items-center justify-center',
                      allOnPageSelected ? 'border-white bg-white' : 'border-gray-600'
                    )}>
                      {allOnPageSelected && <Check className="h-3 w-3 text-black" />}
                    </div>
                  </button>
                </th>
                <th className="w-12 px-2 py-2" />
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400">Tytuł</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-400 w-28">Cena</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-400 w-20">Zapas</th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-400 w-24">Status</th>
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <OfferRow
                  key={offer.id}
                  offer={offer}
                  isSelected={selected.has(offer.id)}
                  isExpanded={expandedId === offer.id}
                  onToggleSelect={toggleOne}
                  onToggleExpand={toggleExpand}
                />
              ))}
              {offers.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-sm text-gray-500">
                    Brak ofert do wyświetlenia
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Strona {page + 1} z {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded-md border border-gray-800 p-1.5 text-gray-400 hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-gray-800 p-1.5 text-gray-400 hover:text-white disabled:opacity-30"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
