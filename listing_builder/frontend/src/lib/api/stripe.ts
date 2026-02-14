// frontend/src/lib/api/stripe.ts
// Purpose: API calls for Stripe subscription management
// NOT for: React hooks or UI logic (those are in hooks/useSubscription.ts)

import { apiRequest } from './client'

export interface SubscriptionStatus {
  tier: string
  status: string
  stripe_customer_id: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
}

export interface CheckoutSession {
  checkout_url: string
}

export interface PortalSession {
  portal_url: string
}

export async function fetchSubscriptionStatus(): Promise<SubscriptionStatus> {
  const response = await apiRequest<SubscriptionStatus>('get', '/stripe/status')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function createCheckoutSession(): Promise<CheckoutSession> {
  const response = await apiRequest<CheckoutSession>('post', '/stripe/checkout')
  if (response.error) throw new Error(response.error)
  return response.data!
}

export async function createPortalSession(): Promise<PortalSession> {
  const response = await apiRequest<PortalSession>('post', '/stripe/portal')
  if (response.error) throw new Error(response.error)
  return response.data!
}
