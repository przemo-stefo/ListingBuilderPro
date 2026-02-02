// frontend/src/lib/api/competitors.ts
// Purpose: Competitors API calls for competitor tracking data
// NOT for: Product CRUD or keyword tracking (separate files)

import { apiRequest } from './client'
import type { CompetitorsResponse, GetCompetitorsParams } from '../types'

// Fetch competitors from backend API
export async function getCompetitors(
  params?: GetCompetitorsParams
): Promise<CompetitorsResponse> {
  const response = await apiRequest<CompetitorsResponse>(
    'get',
    '/api/competitors',
    undefined,
    {
      marketplace: params?.marketplace,
      search: params?.search,
    }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
