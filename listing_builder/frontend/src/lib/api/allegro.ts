// frontend/src/lib/api/allegro.ts
// Purpose: API calls for Allegro offer publishing
// NOT for: OAuth flow (that's oauth.ts) or UI logic

import { apiRequest } from './client'

interface AllegroUpdateResponse {
  status: string
  offer_id: string
}

export async function updateAllegroOffer(
  offerId: string,
  data: { title: string; description_html: string }
): Promise<AllegroUpdateResponse> {
  const response = await apiRequest<AllegroUpdateResponse>(
    'patch',
    `/allegro/offer/${offerId}`,
    data
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}
