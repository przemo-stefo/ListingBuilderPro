// frontend/src/lib/api/stripe.ts
// Purpose: API calls for Stripe license-key payment flow
// NOT for: React hooks or UI logic

import { apiRequest } from './client'

export interface CheckoutRequest {
  plan_type: 'monthly'
  email: string
}

export interface CheckoutResponse {
  checkout_url: string
}

export interface ValidateLicenseResponse {
  valid: boolean
  tier: string
}

export interface RecoverLicenseResponse {
  found: boolean
  license_key: string | null
}

export interface SessionLicenseResponse {
  license_key: string | null
  status: string
}

export async function createCheckoutSession(req: CheckoutRequest): Promise<CheckoutResponse> {
  const response = await apiRequest<CheckoutResponse>('post', '/stripe/create-checkout', req)
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function validateLicense(licenseKey: string): Promise<ValidateLicenseResponse> {
  const response = await apiRequest<ValidateLicenseResponse>('post', '/stripe/validate-license', {
    license_key: licenseKey,
  })
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function recoverLicense(email: string): Promise<RecoverLicenseResponse> {
  const response = await apiRequest<RecoverLicenseResponse>('post', '/stripe/recover-license', { email })
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function getSessionLicense(sessionId: string): Promise<SessionLicenseResponse> {
  const response = await apiRequest<SessionLicenseResponse>('get', `/stripe/session/${sessionId}/license`)
  if (response.error) throw new Error(response.error)
  return response.data!
}
