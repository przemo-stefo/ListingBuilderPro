// frontend/src/lib/api/oauth.ts
// Purpose: API calls for OAuth marketplace connections
// NOT for: React hooks or UI logic (those are in hooks/useOAuth.ts)

import { apiRequest } from './client'
import type { OAuthConnectionsResponse, OAuthAuthorizeResponse } from '../types'

export async function fetchOAuthConnections(): Promise<OAuthConnectionsResponse> {
  const response = await apiRequest<OAuthConnectionsResponse>('get', '/oauth/connections')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getAuthorizeUrl(marketplace: string): Promise<OAuthAuthorizeResponse> {
  const response = await apiRequest<OAuthAuthorizeResponse>('get', `/oauth/${marketplace}/authorize`)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function disconnectMarketplace(marketplace: string): Promise<void> {
  const response = await apiRequest<void>('delete', `/oauth/${marketplace}`)
  if (response.error) throw new Error(response.error)
}
