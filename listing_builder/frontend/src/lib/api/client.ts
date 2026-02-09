// frontend/src/lib/api/client.ts
// Purpose: Axios HTTP client with interceptors and error handling
// NOT for: Business logic or component-specific code

import axios, { AxiosError, AxiosInstance } from 'axios'
import type { ApiError, ApiResponse } from '../types'

// Route all API calls through Next.js proxy (/api/proxy/*)
// The proxy adds the API key server-side — never exposed to browser
const API_URL = '/api/proxy'

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - prevent caching on GET requests
apiClient.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
    }

    if (error.response) {
      // Server responded with error status
      const data = error.response.data as Record<string, unknown>
      apiError.message = (data.detail as string) || (data.message as string) || error.message
      apiError.code = String(error.response.status)
      apiError.details = data
    } else if (error.request) {
      // Request made but no response
      apiError.message = 'No response from server. Please check your connection.'
    } else {
      // Error in request setup
      apiError.message = error.message
    }

    return Promise.reject(apiError)
  }
)

// Generic API wrapper with error handling
export async function apiRequest<T>(
  method: 'get' | 'post' | 'put' | 'delete' | 'patch',
  url: string,
  data?: unknown,
  params?: Record<string, unknown>
): Promise<ApiResponse<T>> {
  try {
    const response = await apiClient({
      method,
      url,
      data,
      params,
    })
    return { data: response.data }
  } catch (error) {
    const apiError = error as ApiError
    return { error: apiError.message }
  }
}

export default apiClient
