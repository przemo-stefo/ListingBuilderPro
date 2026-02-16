// frontend/src/lib/hooks/useAllegroOffers.ts
// Purpose: React Query hooks for Allegro Offers Manager
// NOT for: Direct API calls (those are in lib/api/allegroOffers.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchOffers,
  fetchOfferDetail,
  updateOffer,
  bulkChangeStatus,
  bulkChangePrice,
} from '../api/allegroOffers'
import type { AllegroOfferUpdateRequest, AllegroBulkPriceChange, AllegroOffersParams } from '../types'
import { useToast } from './useToast'

const STALE_TIME = 30_000

export function useOffersList(params: AllegroOffersParams) {
  return useQuery({
    queryKey: ['allegro-offers', params],
    queryFn: () => fetchOffers(params),
    staleTime: STALE_TIME,
  })
}

export function useOfferDetail(offerId: string | null) {
  return useQuery({
    queryKey: ['allegro-offer', offerId],
    queryFn: () => fetchOfferDetail(offerId!),
    staleTime: STALE_TIME,
    enabled: !!offerId,
  })
}

export function useUpdateOffer() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ offerId, data }: { offerId: string; data: AllegroOfferUpdateRequest }) =>
      updateOffer(offerId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['allegro-offers'] })
      qc.invalidateQueries({ queryKey: ['allegro-offer'] })
      toast({ title: 'Oferta zaktualizowana' })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd aktualizacji oferty', description: error.message, variant: 'destructive' })
    },
  })
}

export function useBulkStatus() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ offerIds, action }: { offerIds: string[]; action: 'ACTIVATE' | 'END' }) =>
      bulkChangeStatus(offerIds, action),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['allegro-offers'] })
      toast({ title: `Zmiana statusu: ${data.count} ofert`, description: 'Allegro przetworzy za chwilę' })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd zmiany statusu', description: error.message, variant: 'destructive' })
    },
  })
}

export function useBulkPrice() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (changes: AllegroBulkPriceChange[]) => bulkChangePrice(changes),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['allegro-offers'] })
      toast({ title: `Zmiana ceny: ${data.count} ofert`, description: 'Allegro przetworzy za chwilę' })
    },
    onError: (error: Error) => {
      toast({ title: 'Błąd zmiany ceny', description: error.message, variant: 'destructive' })
    },
  })
}
