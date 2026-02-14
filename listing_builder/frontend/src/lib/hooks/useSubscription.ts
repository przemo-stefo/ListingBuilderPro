// frontend/src/lib/hooks/useSubscription.ts
// Purpose: React Query hooks for Stripe subscription
// NOT for: Direct API calls (those are in lib/api/stripe.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchSubscriptionStatus,
  createCheckoutSession,
  createPortalSession,
} from '../api/stripe'
import { useToast } from './useToast'

export function useSubscriptionStatus() {
  return useQuery({
    queryKey: ['subscription-status'],
    queryFn: fetchSubscriptionStatus,
    staleTime: 30_000,
    // WHY: Retry once — backend might be cold on free tier
    retry: 1,
  })
}

export function useCheckout() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: createCheckoutSession,
    onSuccess: (data) => {
      // WHY: Redirect to Stripe hosted checkout page
      window.location.href = data.checkout_url
    },
    onError: (error: Error) => {
      toast({
        title: 'Błąd płatności',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

export function usePortal() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: createPortalSession,
    onSuccess: (data) => {
      window.location.href = data.portal_url
    },
    onError: (error: Error) => {
      toast({
        title: 'Błąd portalu',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
