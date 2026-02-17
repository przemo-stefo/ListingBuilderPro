// frontend/src/lib/api/research.ts
// Purpose: API client for audience research endpoint
// NOT for: React hooks or UI logic

import { apiRequest } from './client'
import type { AudienceResearchRequest, AudienceResearchResponse } from '../types'

export async function researchAudience(
  payload: AudienceResearchRequest
): Promise<AudienceResearchResponse> {
  const response = await apiRequest<AudienceResearchResponse>(
    'post',
    '/research/audience',
    payload
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
