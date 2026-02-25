// frontend/src/components/providers/TierProvider.tsx
// Purpose: React Context for tier system — license key validation via backend
// NOT for: Payment processing or Stripe API calls

'use client'

import { createContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import type { TierLevel, TierContext } from '@/lib/types/tier'
import { FREE_DAILY_LIMIT } from '@/lib/types/tier'

const LICENSE_KEY_STORAGE = 'lbp_license_key'

function getUsageKey(): string {
  const today = new Date().toISOString().slice(0, 10)
  return `free_usage_${today}`
}

function getStoredLicenseKey(): string {
  if (typeof window === 'undefined') return ''
  return localStorage.getItem(LICENSE_KEY_STORAGE) || ''
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
  licenseKey: '',
  isLoading: true,
})

export function TierProvider({ children }: { children: ReactNode }) {
  const { user, session, loading: authLoading } = useAuth()
  // WHY: Start as 'free' + loading=true during SSR — useEffect reads localStorage on client
  const [tier, setTier] = useState<TierLevel>('free')
  const [usageToday, setUsageToday] = useState(0)
  const [licenseKey, setLicenseKey] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  // WHY: Read localStorage on client mount — NOT from SSR closure (which is always '')
  useEffect(() => {
    const key = localStorage.getItem(LICENSE_KEY_STORAGE) || ''
    const usage = parseInt(localStorage.getItem(getUsageKey()) || '0', 10)
    setUsageToday(usage)

    if (!key) {
      setIsLoading(false)
      return
    }

    // WHY: Set premium + stop loading immediately — no flash, no waiting for backend
    setLicenseKey(key)
    setTier('premium')
    setIsLoading(false)

    // WHY: Validate async in background — downgrade only if backend explicitly says invalid
    fetch('/api/proxy/stripe/validate-license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: key }),
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (!data?.valid) {
          localStorage.removeItem(LICENSE_KEY_STORAGE)
          setLicenseKey('')
          setTier('free')
        }
      })
      .catch(() => {
        // WHY: Backend unavailable — trust stored key as fallback
      })
  }, [])

  // WHY: Auto-recover license after login — if user has a license in DB, activate it
  // without requiring manual key entry
  useEffect(() => {
    if (authLoading || !user?.email || !session?.access_token) return
    // WHY: Skip if already premium — no need to recover
    if (localStorage.getItem(LICENSE_KEY_STORAGE)) return

    // WHY: JWT required by backend — proves caller owns the email they're querying
    fetch('/api/proxy/stripe/recover-license', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({ email: user.email }),
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.found && data?.license_key) {
          localStorage.setItem(LICENSE_KEY_STORAGE, data.license_key)
          setLicenseKey(data.license_key)
          setTier('premium')
          setIsLoading(false)
        }
      })
      .catch(() => {})
  }, [authLoading, user?.email, session?.access_token])

  const isPremium = tier === 'premium'

  const handleUnlock = useCallback((key?: string) => {
    if (key) {
      localStorage.setItem(LICENSE_KEY_STORAGE, key)
      setLicenseKey(key)
      setTier('premium')
      setIsLoading(false)
    }
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
      value={{ tier, usageToday, canOptimize, incrementUsage, unlockPremium: handleUnlock, isPremium, licenseKey, isLoading }}
    >
      {children}
    </TierCtx.Provider>
  )
}
