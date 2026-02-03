// frontend/src/lib/api/converter.ts
// Purpose: API calls for the Allegro→Marketplace converter pipeline
// NOT for: React hooks or UI logic (those are in hooks/useConverter.ts)

import { apiClient, apiRequest } from './client'
import type {
  ConverterMarketplace,
  ConvertRequest,
  ConvertResponse,
  ScrapeResponse,
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
