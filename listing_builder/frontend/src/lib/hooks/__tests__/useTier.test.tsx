// frontend/src/lib/hooks/__tests__/useTier.test.tsx
// Purpose: Tests for useTier hook — reads TierCtx context correctly
// NOT for: TierProvider logic or license validation

import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { type ReactNode } from 'react'
import { TierCtx } from '@/components/providers/TierProvider'
import { useTier } from '../useTier'
import type { TierContext } from '@/lib/types/tier'

function createWrapper(value: TierContext) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <TierCtx.Provider value={value}>{children}</TierCtx.Provider>
  }
}

describe('useTier', () => {
  it('returns free tier context by default', () => {
    const ctx: TierContext = {
      tier: 'free',
      usageToday: 0,
      canOptimize: () => true,
      incrementUsage: () => {},
      unlockPremium: () => {},
      isPremium: false,
      licenseKey: '',
      isLoading: false,
    }

    const { result } = renderHook(() => useTier(), {
      wrapper: createWrapper(ctx),
    })

    expect(result.current.tier).toBe('free')
    expect(result.current.isPremium).toBe(false)
    expect(result.current.licenseKey).toBe('')
    expect(result.current.canOptimize()).toBe(true)
  })

  it('returns premium tier context', () => {
    const ctx: TierContext = {
      tier: 'premium',
      usageToday: 10,
      canOptimize: () => true,
      incrementUsage: () => {},
      unlockPremium: () => {},
      isPremium: true,
      licenseKey: 'abc-123',
      isLoading: false,
    }

    const { result } = renderHook(() => useTier(), {
      wrapper: createWrapper(ctx),
    })

    expect(result.current.tier).toBe('premium')
    expect(result.current.isPremium).toBe(true)
    expect(result.current.licenseKey).toBe('abc-123')
  })

  it('reflects loading state', () => {
    const ctx: TierContext = {
      tier: 'free',
      usageToday: 0,
      canOptimize: () => true,
      incrementUsage: () => {},
      unlockPremium: () => {},
      isPremium: false,
      licenseKey: '',
      isLoading: true,
    }

    const { result } = renderHook(() => useTier(), {
      wrapper: createWrapper(ctx),
    })

    expect(result.current.isLoading).toBe(true)
  })

  it('reports canOptimize as false when limit reached', () => {
    const ctx: TierContext = {
      tier: 'free',
      usageToday: 3,
      canOptimize: () => false,
      incrementUsage: () => {},
      unlockPremium: () => {},
      isPremium: false,
      licenseKey: '',
      isLoading: false,
    }

    const { result } = renderHook(() => useTier(), {
      wrapper: createWrapper(ctx),
    })

    expect(result.current.canOptimize()).toBe(false)
    expect(result.current.usageToday).toBe(3)
  })
})
