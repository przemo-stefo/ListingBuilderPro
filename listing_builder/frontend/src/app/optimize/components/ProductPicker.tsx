// frontend/src/app/optimize/components/ProductPicker.tsx
// Purpose: Search-as-you-type combobox to pick a product from the database
// NOT for: Manual input (that's the form fields below this component)

'use client'

import { useState, useRef, useEffect } from 'react'
import { Search, X, Loader2, Database } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { listProducts } from '@/lib/api/products'
import { cn } from '@/lib/utils'
import type { Product } from '@/lib/types'

interface ProductPickerProps {
  onSelect: (product: Product) => void
  onClear: () => void
  selectedTitle?: string
}

export function ProductPicker({ onSelect, onClear, selectedTitle }: ProductPickerProps) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [debounced, setDebounced] = useState('')
  const wrapperRef = useRef<HTMLDivElement>(null)

  // WHY: Debounce 300ms to avoid hammering the API on every keystroke
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  // WHY: Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // WHY: Only fetch when dropdown is open — avoids wasting API calls on page mount
  const { data, isLoading } = useQuery({
    queryKey: ['product-picker', debounced],
    queryFn: () => listProducts({ search: debounced || undefined, page: 1, page_size: 20, sort_by: 'created_at', sort_order: 'desc' }),
    enabled: open,
    staleTime: 30000,
  })

  const products = data?.items ?? []

  const handleSelect = (product: Product) => {
    onSelect(product)
    setQuery('')
    setOpen(false)
  }

  // WHY: If a product is already selected, show it as a chip with clear button
  if (selectedTitle) {
    return (
      <div className="rounded-lg border border-gray-700 bg-[#1A1A1A] p-3">
        <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
          <Database className="h-3.5 w-3.5" />
          Wybrany produkt z bazy
        </div>
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-white truncate">{selectedTitle}</span>
          <button
            onClick={onClear}
            className="shrink-0 rounded-md border border-gray-700 px-2.5 py-1 text-xs text-gray-400 hover:border-gray-500 hover:text-white transition-colors"
          >
            <X className="h-3 w-3 inline mr-1" />
            Wyczyść
          </button>
        </div>
      </div>
    )
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3">
        <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
          <Database className="h-3.5 w-3.5" />
          Wybierz produkt z bazy
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
            onFocus={() => setOpen(true)}
            placeholder="Szukaj po nazwie, ASIN, marce..."
            className="w-full rounded-lg border border-gray-800 bg-[#121212] py-2 pl-10 pr-4 text-sm text-white placeholder-gray-600 outline-none focus:border-gray-600"
          />
          {isLoading && (
            <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-gray-500" />
          )}
        </div>
      </div>

      {/* WHY: Dropdown list of matching products */}
      {open && products.length > 0 && (
        <div className="absolute z-40 mt-1 w-full max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-[#1A1A1A] shadow-xl">
          {products.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelect(p)}
              className="flex w-full items-start gap-3 px-4 py-2.5 text-left hover:bg-gray-800 transition-colors border-b border-gray-800/50 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm text-white truncate">{p.title_original}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  {p.brand && <span className="text-[10px] text-gray-500">{p.brand}</span>}
                  {p.source_id && <span className="text-[10px] font-mono text-gray-600">{p.source_id}</span>}
                  {p.category && <span className="text-[10px] text-gray-600 truncate">{p.category}</span>}
                </div>
              </div>
              <span className={cn(
                'shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase',
                p.status === 'optimized' ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
              )}>
                {p.status}
              </span>
            </button>
          ))}
        </div>
      )}

      {open && !isLoading && debounced && products.length === 0 && (
        <div className="absolute z-40 mt-1 w-full rounded-lg border border-gray-700 bg-[#1A1A1A] p-4 text-center text-sm text-gray-500 shadow-xl">
          Brak produktów pasujących do &quot;{debounced}&quot;
        </div>
      )}

      <p className="mt-2 text-center text-xs text-gray-600">lub wpisz ręcznie poniżej</p>
    </div>
  )
}
