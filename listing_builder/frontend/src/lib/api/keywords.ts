// frontend/src/lib/api/keywords.ts
// Purpose: Keywords API calls for SEO keyword tracking data
// NOT for: Product CRUD or optimization (separate files)

import { apiRequest } from './client'
import type { KeywordsResponse, GetKeywordsParams } from '../types'

// Fetch keywords from backend API
export async function getKeywords(
  params?: GetKeywordsParams
): Promise<KeywordsResponse> {
  const response = await apiRequest<KeywordsResponse>(
    'get',
    '/api/keywords',
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
