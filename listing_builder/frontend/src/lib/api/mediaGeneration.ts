// frontend/src/lib/api/mediaGeneration.ts
// Purpose: API calls for background media generation (start, poll, history, feedback)
// NOT for: React hooks or UI components

import { apiRequest } from './client'

export interface MediaGenStartParams {
  media_type: 'video' | 'images'
  product_name?: string
  brand?: string
  bullet_points?: string[]
  description?: string
  theme?: string
  llm_provider?: string
  url?: string
  prompt?: string
}

export interface MediaGenJob {
  id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  media_type: 'video' | 'images'
  created_at: string
  completed_at: string | null
  error_message: string | null
}

export interface MediaGenHistoryItem extends MediaGenJob {
  product_name: string
  brand: string
  theme: string
  url: string
  feedback: string | null
  image_count: number | null
}

export interface MediaGenHistoryList {
  items: MediaGenHistoryItem[]
  total: number
  page: number
}

export async function startGeneration(params: MediaGenStartParams): Promise<{ id: number; status: string }> {
  const res = await apiRequest<{ id: number; status: string }>('post', '/media-gen/start', params)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function getGenerationStatus(id: number): Promise<MediaGenJob> {
  const res = await apiRequest<MediaGenJob>('get', `/media-gen/status/${id}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function getGenerationResult(id: number): Promise<{ id: number; result_data: Record<string, unknown> }> {
  const res = await apiRequest<{ id: number; result_data: Record<string, unknown> }>('get', `/media-gen/result/${id}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function getMediaHistory(page = 1): Promise<MediaGenHistoryList> {
  const res = await apiRequest<MediaGenHistoryList>('get', '/media-gen/history', undefined, { page })
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function getActiveJobs(): Promise<{ jobs: { id: number; status: string; media_type: string }[] }> {
  const res = await apiRequest<{ jobs: { id: number; status: string; media_type: string }[] }>('get', '/media-gen/active')
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function saveFeedback(id: number, feedback: string): Promise<void> {
  const res = await apiRequest<{ status: string }>('patch', `/media-gen/${id}/feedback`, { feedback })
  if (res.error) throw new Error(res.error)
}

export async function deleteGeneration(id: number): Promise<void> {
  const res = await apiRequest<{ status: string }>('delete', `/media-gen/${id}`)
  if (res.error) throw new Error(res.error)
}
