// frontend/src/lib/api/validator.ts
// Purpose: API client for Product Validator endpoints
// NOT for: UI logic or state management

import { apiClient } from './client'
import type { ValidatorResponse, ValidatorHistoryResponse } from '../types'

export async function analyzeProduct(
  productInput: string,
  marketplace: string = 'amazon',
): Promise<ValidatorResponse> {
  const { data } = await apiClient.post<ValidatorResponse>('/validator/analyze', {
    product_input: productInput,
    marketplace,
  })
  return data
}

export async function getValidatorHistory(
  limit: number = 20,
  offset: number = 0,
): Promise<ValidatorHistoryResponse> {
  const { data } = await apiClient.get<ValidatorHistoryResponse>('/validator/history', {
    params: { limit, offset },
  })
  return data
}

export async function deleteValidatorHistory(id: number): Promise<void> {
  await apiClient.delete(`/validator/history/${id}`)
}
