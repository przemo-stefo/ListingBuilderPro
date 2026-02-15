// frontend/src/lib/api/converter.ts
// Purpose: API calls for the Allegro→Marketplace converter pipeline
// NOT for: React hooks or UI logic (those are in hooks/useConverter.ts)

import { apiClient, apiRequest } from './client'
import type {
  ConverterMarketplace,
  ConvertRequest,
  ConvertResponse,
  ScrapeResponse,
  StoreUrlsResponse,
  StoreConvertRequest,
  StoreJobStatus,
} from '../types'

// WHY: Converter requests can take 30s+ for batch scraping, so we need longer timeout
const CONVERTER_TIMEOUT = 120_000

export async function getMarketplaces(): Promise<ConverterMarketplace[]> {
  const response = await apiRequest<{ marketplaces: ConverterMarketplace[] }>(
    'get',
    '/converter/marketplaces'
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!.marketplaces
}

export async function scrapeAllegro(
  urls: string[],
  delay: number = 3.0
): Promise<ScrapeResponse> {
  const response = await apiRequest<ScrapeResponse>(
    'post',
    '/converter/scrape',
    { urls, delay }
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

export async function convertProducts(
  payload: ConvertRequest
): Promise<ConvertResponse> {
  const response = await apiRequest<ConvertResponse>(
    'post',
    '/converter/convert',
    payload
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// WHY: Download returns binary file, so we use apiClient directly with blob response
export async function downloadTemplate(payload: ConvertRequest): Promise<Blob> {
  const response = await apiClient.post('/converter/download', payload, {
    responseType: 'blob',
    timeout: CONVERTER_TIMEOUT,
  })

  return response.data
}


// ── Store converter API ─────────────────────────────────────────────────

export async function getStoreUrls(store: string): Promise<StoreUrlsResponse> {
  const response = await apiRequest<StoreUrlsResponse>(
    'post',
    '/converter/store-urls',
    { store }
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function startStoreConvert(
  payload: StoreConvertRequest
): Promise<{ job_id: string; total: number; status: string }> {
  const response = await apiRequest<{ job_id: string; total: number; status: string }>(
    'post',
    '/converter/store-convert',
    payload
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getStoreJobStatus(jobId: string): Promise<StoreJobStatus> {
  const response = await apiRequest<StoreJobStatus>(
    'get',
    `/converter/store-job/${jobId}`
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function downloadStoreJob(jobId: string): Promise<Blob> {
  const response = await apiClient.get(`/converter/store-job/${jobId}/download`, {
    responseType: 'blob',
    timeout: CONVERTER_TIMEOUT,
  })
  return response.data
}


// ── Allegro OAuth + API ─────────────────────────────────────────────────

export async function getOAuthConnections(): Promise<
  Array<{ marketplace: string; status: string; seller_name: string | null }>
> {
  const response = await apiRequest<{
    connections: Array<{ marketplace: string; status: string; seller_name: string | null }>
  }>('get', '/oauth/connections')
  if (response.error) throw new Error(response.error)
  return response.data!.connections
}

export async function startAllegroOAuth(): Promise<{ authorize_url: string }> {
  const response = await apiRequest<{ authorize_url: string }>(
    'get',
    '/oauth/allegro/authorize'
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getAllegroOffers(): Promise<StoreUrlsResponse> {
  const response = await apiRequest<StoreUrlsResponse>(
    'get',
    '/converter/allegro-offers'
  )
  if (response.error) throw new Error(response.error)
  return response.data!
}
