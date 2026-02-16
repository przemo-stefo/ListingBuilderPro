// frontend/src/lib/api/allegroOffers.ts
// Purpose: API calls for Allegro Offers Manager — list, edit, bulk operations
// NOT for: React hooks or UI logic (those are in hooks/useAllegroOffers.ts)

import { apiRequest } from './client'
import type {
  AllegroOffersListResponse,
  AllegroOfferDetail,
  AllegroOfferUpdateRequest,
  BulkCommandResponse,
  AllegroBulkPriceChange,
  AllegroOffersParams,
} from '../types'

export async function fetchOffers(params?: AllegroOffersParams): Promise<AllegroOffersListResponse> {
  const response = await apiRequest<AllegroOffersListResponse>(
    'get', '/allegro/offers', undefined, params as Record<string, unknown>
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function fetchOfferDetail(offerId: string): Promise<AllegroOfferDetail> {
  const response = await apiRequest<AllegroOfferDetail>('get', `/allegro/offers/${offerId}`)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function updateOffer(offerId: string, data: AllegroOfferUpdateRequest): Promise<void> {
  const response = await apiRequest<void>('patch', `/allegro/offers/${offerId}`, data)
  if (response.error) throw new Error(response.error)
}

export async function bulkChangeStatus(
  offerIds: string[], action: 'ACTIVATE' | 'END'
): Promise<BulkCommandResponse> {
  const response = await apiRequest<BulkCommandResponse>(
    'post', '/allegro/offers/bulk-status', { offer_ids: offerIds, action }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function bulkChangePrice(
  changes: AllegroBulkPriceChange[]
): Promise<BulkCommandResponse> {
  const response = await apiRequest<BulkCommandResponse>(
    'post', '/allegro/offers/bulk-price', { changes }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}
