// frontend/src/lib/api/optimizerHistory.ts
// Purpose: API calls for optimizer history (list, detail, delete)
// NOT for: React hooks (those are in hooks/useOptimizerHistory.ts)

import { apiRequest } from './client'
import type { OptimizationHistoryList, OptimizationHistoryDetail, OptimizerResponse } from '../types'

export async function getHistory(page = 1): Promise<OptimizationHistoryList> {
  const res = await apiRequest<OptimizationHistoryList>('get', '/optimizer/history', undefined, { page })
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function getHistoryDetail(id: number): Promise<OptimizationHistoryDetail> {
  const res = await apiRequest<OptimizationHistoryDetail>('get', `/optimizer/history/${id}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function deleteHistory(id: number): Promise<void> {
  const res = await apiRequest<{ status: string }>('delete', `/optimizer/history/${id}`)
  if (res.error) throw new Error(res.error)
}

export async function improveFromHistory(id: number): Promise<OptimizerResponse> {
  const res = await apiRequest<OptimizerResponse>('post', `/optimizer/history/${id}/improve`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function createShareLink(data: {
  listing: OptimizerResponse['listing']
  scores?: OptimizerResponse['scores']
  compliance?: OptimizerResponse['compliance']
  product_title: string
  brand: string
  marketplace: string
}): Promise<string> {
  const res = await apiRequest<{ token: string }>('post', '/optimizer/share', data)
  if (res.error) throw new Error(res.error)
  return res.data!.token
}
