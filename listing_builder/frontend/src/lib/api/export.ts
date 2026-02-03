// frontend/src/lib/api/export.ts
// Purpose: Publishing/export API calls to marketplaces
// NOT for: Product optimization or import operations

import { apiRequest } from './client'
import type {
  PublishRequest,
  PublishResponse,
  BulkPublishRequest,
  BulkPublishResponse,
  Marketplace,
} from '../types'

// Publish single product to marketplace
export async function publishProduct(
  productId: string,
  marketplace: string,
  publishImmediately: boolean = false
): Promise<PublishResponse> {
  const request: PublishRequest = {
    product_id: productId,
    marketplace,
    publish_immediately: publishImmediately,
  }

  const response = await apiRequest<PublishResponse>(
    'post',
    `/api/export/publish/${productId}`,
    request
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Bulk publish multiple products
export async function bulkPublish(
  productIds: string[],
  marketplace: string,
  publishImmediately: boolean = false
): Promise<BulkPublishResponse> {
  const request: BulkPublishRequest = {
    product_ids: productIds,
    marketplace,
    publish_immediately: publishImmediately,
  }

  const response = await apiRequest<BulkPublishResponse>(
    'post',
    '/export/bulk-publish',
    request
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}

// Get list of available marketplaces
export async function listMarketplaces(): Promise<Marketplace[]> {
  const response = await apiRequest<Marketplace[]>(
    'get',
    '/export/marketplaces'
  )

  if (response.error) {
    throw new Error(response.error)
  }

  return response.data!
}
