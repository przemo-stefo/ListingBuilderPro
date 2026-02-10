// frontend/src/components/providers/TierProvider.tsx
// Purpose: React Context for tier system — persists to localStorage, supports URL unlock
// NOT for: Backend enforcement or payment processing

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
function UnlockHandler({ onUnlock }: { onUnlock: () => void }) {
  const searchParams = useSearchParams()
  useEffect(() => {
    if (searchParams.get('unlock') === 'premium') {
      onUnlock()
    }
  }, [searchParams, onUnlock])
  return null
}

export function TierProvider({ children }: { children: ReactNode }) {
  const [tier, setTier] = useState<TierLevel>('free')
  const [usageToday, setUsageToday] = useState(0)

  // WHY: Hydrate from localStorage on mount
  useEffect(() => {
    setTier(getStoredTier())
    setUsageToday(getStoredUsage())
  }, [])

  const isPremium = tier === 'premium'

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
        <UnlockHandler onUnlock={handleUnlock} />
      </Suspense>
      {children}
    </TierCtx.Provider>
  )
}
