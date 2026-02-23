// frontend/src/app/products/import/components/AllegroImport.tsx
// Purpose: Import products from connected Allegro account — select offers and import to DB
// NOT for: Allegro Manager (editing offers) or converter (direct marketplace conversion)

'use client'

import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useOAuthConnections } from '@/lib/hooks/useOAuth'
import { useOffersList } from '@/lib/hooks/useAllegroOffers'
import { importFromAllegro } from '@/lib/api/import'
import { useToast } from '@/lib/hooks/useToast'
import { cn } from '@/lib/utils'
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Loader2,
  Link2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import type { AllegroOffersParams } from '@/lib/types'

const PAGE_SIZE = 20

export default function AllegroImport() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  // OAuth check
  const { data: oauthData, isLoading: oauthLoading } = useOAuthConnections()
  const allegroConn = oauthData?.connections?.find(
    (c) => c.marketplace === 'allegro' && c.status === 'active'
  )

  // Offers list
  const [params, setParams] = useState<AllegroOffersParams>({
    limit: PAGE_SIZE,
    offset: 0,
    status: 'ACTIVE',
  })
  const { data: offersData, isLoading: offersLoading } = useOffersList(params)

  // Selection
  const [selected, setSelected] = useState<Set<string>>(new Set())

  // Import result
  const [result, setResult] = useState<{
    success_count: number
    failed_count: number
    errors: string[]
  } | null>(null)

  const importMutation = useMutation({
    mutationFn: (ids: string[]) => importFromAllegro(ids),
    onSuccess: (data) => {
      setResult(data)
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['products'] })
      toast({
        title: `Zaimportowano ${data.success_count} produktów`,
        description: data.failed_count > 0 ? `${data.failed_count} nie udało się` : undefined,
      })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd importu', description: error.message, variant: 'destructive' })
    },
  })

  const allOnPage = useMemo(
    () => offersData?.offers?.map((o) => o.id) ?? [],
    [offersData]
  )

  const allSelected = allOnPage.length > 0 && allOnPage.every((id) => selected.has(id))

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (allSelected) {
      setSelected((prev) => {
        const next = new Set(prev)
        allOnPage.forEach((id) => next.delete(id))
        return next
      })
    } else {
      setSelected((prev) => {
        const next = new Set(prev)
        allOnPage.forEach((id) => next.add(id))
        return next
      })
    }
  }

  const currentPage = Math.floor((params.offset ?? 0) / PAGE_SIZE) + 1
  const totalPages = offersData ? Math.ceil(offersData.total / PAGE_SIZE) : 0

  // Loading OAuth
  if (oauthLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  // Not connected — CTA
  if (!allegroConn) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-8 text-center">
        <Link2 className="mx-auto h-10 w-10 text-gray-500 mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Połącz konto Allegro</h3>
        <p className="text-sm text-gray-400 mb-6">
          Aby importować oferty z konta, najpierw połącz Allegro przez OAuth.
        </p>
        <Link
          href="/integrations"
          className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black hover:bg-gray-200 transition-colors"
        >
          <Link2 className="h-4 w-4" />
          Przejdź do Integracji
        </Link>
      </div>
    )
  }

  // Import result view
  if (result) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-8 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-green-500 mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">Import zakończony</h3>
        <p className="text-sm text-gray-400 mb-1">
          Zaimportowano: <span className="text-green-400 font-medium">{result.success_count}</span>
          {result.failed_count > 0 && (
            <> | Błędy: <span className="text-red-400 font-medium">{result.failed_count}</span></>
          )}
        </p>
        {result.errors.length > 0 && (
          <div className="mt-3 max-h-32 overflow-y-auto rounded bg-gray-900 p-3 text-left">
            {result.errors.map((err, i) => (
              <p key={i} className="text-xs text-red-400">{err}</p>
            ))}
          </div>
        )}
        <div className="mt-6 flex justify-center gap-3">
          <Link
            href="/products"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black hover:bg-gray-200 transition-colors"
          >
            Zobacz produkty
          </Link>
          <button
            onClick={() => setResult(null)}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:border-gray-500 transition-colors"
          >
            Importuj więcej
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with selection info */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          Konto: <span className="text-white">{allegroConn.seller_name || 'Allegro'}</span>
          {offersData && <span className="ml-2">({offersData.total} ofert)</span>}
        </p>
        {selected.size > 0 && (
          <button
            onClick={() => importMutation.mutate(Array.from(selected))}
            disabled={importMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            {importMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Importuj {selected.size} {selected.size === 1 ? 'ofertę' : selected.size < 5 ? 'oferty' : 'ofert'}
          </button>
        )}
      </div>

      {/* Offers table */}
      {offersLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : !offersData?.offers?.length ? (
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-8 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-gray-500 mb-3" />
          <p className="text-gray-400">Brak aktywnych ofert na koncie Allegro</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-[#121212]">
                <th className="px-3 py-2 text-left">
                  <button onClick={toggleAll} className="flex items-center justify-center">
                    <div className={cn(
                      'h-4 w-4 rounded border flex items-center justify-center',
                      allSelected ? 'border-white bg-white' : 'border-gray-600'
                    )}>
                      {allSelected && <Check className="h-3 w-3 text-black" />}
                    </div>
                  </button>
                </th>
                <th className="px-2 py-2 text-left text-gray-500 font-medium w-10" />
                <th className="px-3 py-2 text-left text-gray-500 font-medium">Nazwa</th>
                <th className="px-3 py-2 text-right text-gray-500 font-medium">Cena</th>
                <th className="px-3 py-2 text-center text-gray-500 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {offersData.offers.map((offer) => (
                <tr
                  key={offer.id}
                  className="border-b border-gray-800/50 hover:bg-white/5 transition-colors"
                >
                  <td className="px-3 py-2">
                    <button
                      onClick={() => toggleSelect(offer.id)}
                      className="flex items-center justify-center"
                    >
                      <div className={cn(
                        'h-4 w-4 rounded border flex items-center justify-center',
                        selected.has(offer.id) ? 'border-white bg-white' : 'border-gray-600'
                      )}>
                        {selected.has(offer.id) && <Check className="h-3 w-3 text-black" />}
                      </div>
                    </button>
                  </td>
                  <td className="px-2 py-2">
                    {offer.image ? (
                      <img src={offer.image} alt="" className="h-8 w-8 rounded object-cover bg-gray-800" />
                    ) : (
                      <div className="h-8 w-8 rounded bg-gray-800" />
                    )}
                  </td>
                  <td className="px-3 py-2 text-white truncate max-w-xs">{offer.name}</td>
                  <td className="px-3 py-2 text-right text-gray-300 font-mono">
                    {offer.price.amount} {offer.price.currency}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span className="inline-block rounded-full bg-green-500/20 px-2 py-0.5 text-xs font-medium text-green-400">
                      {offer.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            disabled={currentPage <= 1}
            onClick={() => setParams((p) => ({ ...p, offset: (p.offset ?? 0) - PAGE_SIZE }))}
            className="rounded-lg border border-gray-700 p-2 text-gray-400 hover:text-white disabled:opacity-30 transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-sm text-gray-400">
            {currentPage} / {totalPages}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => setParams((p) => ({ ...p, offset: (p.offset ?? 0) + PAGE_SIZE }))}
            className="rounded-lg border border-gray-700 p-2 text-gray-400 hover:text-white disabled:opacity-30 transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
