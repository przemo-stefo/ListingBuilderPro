// frontend/src/components/providers/TierProvider.tsx
// Purpose: React Context for tier system — backend-first with localStorage fallback
// NOT for: Payment processing or Stripe API calls

'use client'

import { createContext, useState, useEffect, useCallback, Suspense, type ReactNode } from 'react'
import { useSearchParams } from 'next/navigation'
import type { TierLevel, TierContext } from '@/lib/types/tier'
import { FREE_DAILY_LIMIT } from '@/lib/types/tier'

const TIER_STORAGE_KEY = 'lbp_tier'

function getUsageKey(): string {
  const today = new Date().toISOString().slice(0, 10)
  return `free_usage_${today}`
}

function getStoredTier(): TierLevel {
  if (typeof window === 'undefined') return 'free'
  return (localStorage.getItem(TIER_STORAGE_KEY) as TierLevel) || 'free'
}

function getStoredUsage(): number {
  if (typeof window === 'undefined') return 0
  return parseInt(localStorage.getItem(getUsageKey()) || '0', 10)
}

export const TierCtx = createContext<TierContext>({
  tier: 'free',
  usageToday: 0,
  canOptimize: () => true,
  incrementUsage: () => {},
  unlockPremium: () => {},
  isPremium: false,
})

// WHY: useSearchParams in a separate component so only IT lives inside Suspense,
// not the entire page tree — fixes Next.js 14 static prerender bail-out
function PaymentHandler({ onPaymentReturn }: { onPaymentReturn: () => void }) {
  const searchParams = useSearchParams()
  useEffect(() => {
    // WHY: Stripe redirects back with ?payment=success — verify via backend, not URL alone
    // SECURITY: removed ?unlock=premium — was a bypass vector
    if (searchParams.get('payment') === 'success') {
      onPaymentReturn()
    }
  }, [searchParams, onPaymentReturn])
  return null
}

export function TierProvider({ children }: { children: ReactNode }) {
  const [tier, setTier] = useState<TierLevel>('free')
  const [usageToday, setUsageToday] = useState(0)

  // WHY: Try backend first, fall back to localStorage
  useEffect(() => {
    setTier(getStoredTier())
    setUsageToday(getStoredUsage())

    // WHY: Fetch real tier from backend — overrides localStorage if backend says premium
    fetch('/api/proxy/stripe/status')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.tier === 'premium' || data?.status === 'active') {
          localStorage.setItem(TIER_STORAGE_KEY, 'premium')
          setTier('premium')
        } else if (data?.tier === 'free' && data?.status !== 'active') {
          // WHY: Backend says free — clear any stale localStorage premium
          localStorage.setItem(TIER_STORAGE_KEY, 'free')
          setTier('free')
        }
      })
      .catch(() => {
        // WHY: Backend unavailable — keep localStorage value as fallback
      })
  }, [])

  const isPremium = tier === 'premium'

  // WHY: After Stripe redirect, re-fetch from backend to verify payment actually went through
  // SECURITY: never trust URL params alone — backend is source of truth
  const handlePaymentReturn = useCallback(() => {
    fetch('/api/proxy/stripe/status')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.tier === 'premium' || data?.status === 'active') {
          localStorage.setItem(TIER_STORAGE_KEY, 'premium')
          setTier('premium')
        }
      })
      .catch(() => {})
  }, [])

  const handleUnlock = useCallback(() => {
    localStorage.setItem(TIER_STORAGE_KEY, 'premium')
    setTier('premium')
  }, [])

  const canOptimize = useCallback(() => {
    if (isPremium) return true
    return usageToday < FREE_DAILY_LIMIT
  }, [isPremium, usageToday])

  const incrementUsage = useCallback(() => {
    if (isPremium) return
    const newCount = usageToday + 1
    setUsageToday(newCount)
    localStorage.setItem(getUsageKey(), String(newCount))
  }, [isPremium, usageToday])

  return (
    <TierCtx.Provider
      value={{ tier, usageToday, canOptimize, incrementUsage, unlockPremium: handleUnlock, isPremium }}
    >
      <Suspense fallback={null}>
        <PaymentHandler onPaymentReturn={handlePaymentReturn} />
      </Suspense>
      {children}
    </TierCtx.Provider>
  )
}
