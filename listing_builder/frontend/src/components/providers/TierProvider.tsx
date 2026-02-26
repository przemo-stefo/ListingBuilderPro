// frontend/src/components/providers/TierProvider.tsx
// Purpose: React Context for tier system — license key validation via backend
// NOT for: Payment processing or Stripe API calls

'use client'

import { createContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { apiClient } from '@/lib/api/client'
import type { TierLevel, TierContext } from '@/lib/types/tier'
import { FREE_DAILY_LIMIT } from '@/lib/types/tier'

const LICENSE_KEY_STORAGE = 'lbp_license_key'
// WHY: Track which user owns the stored license key — prevents cross-user leakage
const LICENSE_OWNER_STORAGE = 'lbp_license_owner'

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

  // WHY: Clear stored license if it belongs to a different user — prevents cross-user leakage
  // Must run BEFORE the license read effect, and re-run when user changes
  useEffect(() => {
    if (authLoading) return
    const storedOwner = localStorage.getItem(LICENSE_OWNER_STORAGE)
    const currentUser = user?.id || null

    if (storedOwner && currentUser && storedOwner !== currentUser) {
      localStorage.removeItem(LICENSE_KEY_STORAGE)
      localStorage.removeItem(LICENSE_OWNER_STORAGE)
      setLicenseKey('')
      setTier('free')
    }
  }, [authLoading, user?.id])

  // WHY: Read localStorage on client mount — NOT from SSR closure (which is always '')
  useEffect(() => {
    if (authLoading) return

    const key = localStorage.getItem(LICENSE_KEY_STORAGE) || ''
    const usage = parseInt(localStorage.getItem(getUsageKey()) || '0', 10)
    setUsageToday(usage)

    // WHY: If stored key belongs to different user, ignore it
    const storedOwner = localStorage.getItem(LICENSE_OWNER_STORAGE)
    if (key && storedOwner && user?.id && storedOwner !== user.id) {
      localStorage.removeItem(LICENSE_KEY_STORAGE)
      localStorage.removeItem(LICENSE_OWNER_STORAGE)
      setIsLoading(false)
      return
    }

    if (!key) {
      setIsLoading(false)
      return
    }

    // WHY: Set premium + stop loading immediately — no flash, no waiting for backend
    setLicenseKey(key)
    setTier('premium')
    setIsLoading(false)

    // WHY: Validate async in background — downgrade only if backend explicitly says invalid
    // WHY: apiClient sends JWT + License-Key (raw fetch() was missing them)
    apiClient.post('/stripe/validate-license', { license_key: key })
      .then((res) => {
        if (!res.data?.valid) {
          localStorage.removeItem(LICENSE_KEY_STORAGE)
          localStorage.removeItem(LICENSE_OWNER_STORAGE)
          setLicenseKey('')
          setTier('free')
        }
      })
      .catch(() => {
        // WHY: Backend unavailable — trust stored key as fallback
      })
  }, [authLoading, user?.id])

  // WHY: Auto-recover license after login — if user has a license in DB, activate it
  // without requiring manual key entry
  useEffect(() => {
    if (authLoading || !user?.email || !session?.access_token) return
    // WHY: Skip if already premium — no need to recover
    if (localStorage.getItem(LICENSE_KEY_STORAGE)) return

    // WHY: apiClient sends JWT automatically — proves caller owns the email
    apiClient.post('/stripe/recover-license', { email: user.email })
      .then((res) => {
        const data = res.data
        if (data?.found && data?.license_key) {
          localStorage.setItem(LICENSE_KEY_STORAGE, data.license_key)
          // WHY: Store user ID alongside key — prevents cross-user leakage on same browser
          localStorage.setItem(LICENSE_OWNER_STORAGE, user.id)
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
      if (user?.id) localStorage.setItem(LICENSE_OWNER_STORAGE, user.id)
      setLicenseKey(key)
      setTier('premium')
      setIsLoading(false)
    }
  }, [user?.id])

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
