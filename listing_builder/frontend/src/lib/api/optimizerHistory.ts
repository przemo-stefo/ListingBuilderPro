// frontend/src/lib/api/optimizerHistory.ts
// Purpose: API calls for optimizer history (list, detail, delete)
// NOT for: React hooks (those are in hooks/useOptimizerHistory.ts)

import { apiRequest } from './client'
import type { OptimizationHistoryList, OptimizationHistoryDetail } from '../types'

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
