// frontend/src/lib/api/__tests__/client.test.ts
// Purpose: Tests for Axios API client — interceptors, license key injection, error handling
// NOT for: Testing actual backend endpoints

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// WHY: Mock axios.create so we can inspect interceptor behavior
vi.mock('axios', async () => {
  const requestInterceptors: Array<{ fulfilled: Function; rejected?: Function }> = []
  const responseInterceptors: Array<{ fulfilled: Function; rejected?: Function }> = []

  const instance = {
    interceptors: {
      request: {
        use: (fulfilled: Function, rejected?: Function) => {
          requestInterceptors.push({ fulfilled, rejected })
        },
      },
      response: {
        use: (fulfilled: Function, rejected?: Function) => {
          responseInterceptors.push({ fulfilled, rejected })
        },
      },
    },
    defaults: { headers: { common: {} } },
    // WHY: Expose interceptors so tests can call them directly
    _requestInterceptors: requestInterceptors,
    _responseInterceptors: responseInterceptors,
  }

  return {
    default: {
      create: vi.fn(() => instance),
      isAxiosError: vi.fn((e: unknown) => e instanceof Error),
    },
    AxiosError: Error,
  }
})

describe('API Client', () => {
  let clientModule: typeof import('../client')
  let mockInstance: ReturnType<typeof axios.create> & {
    _requestInterceptors: Array<{ fulfilled: Function }>
    _responseInterceptors: Array<{ fulfilled: Function; rejected?: Function }>
  }

  beforeEach(async () => {
    vi.resetModules()
    localStorage.clear()
    // WHY: Re-import to re-run interceptor setup
    clientModule = await import('../client')
    mockInstance = axios.create() as typeof mockInstance
  })

  it('creates client with correct baseURL', () => {
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: '/api/proxy',
        timeout: 30000,
      })
    )
  })

  describe('request interceptor', () => {
    it('adds cache-busting param on GET requests', () => {
      const interceptor = mockInstance._requestInterceptors[0]
      const config = { method: 'get', params: {}, headers: {} as Record<string, string> }
      const result = interceptor.fulfilled(config)
      expect(result.params._t).toBeDefined()
    })

    it('does not add cache-busting on POST', () => {
      const interceptor = mockInstance._requestInterceptors[0]
      const config = { method: 'post', params: {}, headers: {} as Record<string, string> }
      const result = interceptor.fulfilled(config)
      expect(result.params._t).toBeUndefined()
    })

    it('injects license key from localStorage', () => {
      localStorage.setItem('lbp_license_key', 'test-key-123')
      const interceptor = mockInstance._requestInterceptors[0]
      const config = { method: 'get', params: {}, headers: {} as Record<string, string> }
      const result = interceptor.fulfilled(config)
      expect(result.headers['X-License-Key']).toBe('test-key-123')
    })

    it('omits license key header when not stored', () => {
      const interceptor = mockInstance._requestInterceptors[0]
      const config = { method: 'get', params: {}, headers: {} as Record<string, string> }
      const result = interceptor.fulfilled(config)
      expect(result.headers['X-License-Key']).toBeUndefined()
    })
  })

  describe('response interceptor', () => {
    it('passes through successful responses', () => {
      const interceptor = mockInstance._responseInterceptors[0]
      const response = { data: { ok: true }, status: 200 }
      expect(interceptor.fulfilled(response)).toBe(response)
    })

    it('transforms server errors into ApiError format', async () => {
      const interceptor = mockInstance._responseInterceptors[0]
      const axiosError = {
        response: {
          status: 422,
          data: { detail: 'Validation failed' },
        },
        message: 'Request failed',
      }

      try {
        await interceptor.rejected!(axiosError)
      } catch (err: unknown) {
        const apiErr = err as { message: string; code: string }
        expect(apiErr.message).toBe('Validation failed')
        expect(apiErr.code).toBe('422')
      }
    })

    it('handles network errors (no response)', async () => {
      const interceptor = mockInstance._responseInterceptors[0]
      const axiosError = { request: {}, message: 'Network Error' }

      try {
        await interceptor.rejected!(axiosError)
      } catch (err: unknown) {
        const apiErr = err as { message: string }
        expect(apiErr.message).toContain('No response from server')
      }
    })
  })
})
