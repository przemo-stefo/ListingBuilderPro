// frontend/src/lib/hooks/useSubscription.ts
// Purpose: React Query hooks for Stripe license-key payments
// NOT for: Direct API calls (those are in lib/api/stripe.ts)

import { useMutation } from '@tanstack/react-query'
import { createCheckoutSession, type CheckoutRequest } from '../api/stripe'
import { useToast } from './useToast'

export function useCheckout() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (req: CheckoutRequest) => createCheckoutSession(req),
    onSuccess: (data) => {
      window.location.href = data.checkout_url
    },
    onError: (error: Error) => {
      toast({
        title: 'Blad platnosci',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
