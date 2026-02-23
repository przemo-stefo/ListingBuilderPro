// frontend/src/components/tier/__tests__/FeatureGate.test.tsx
// Purpose: Tests for FeatureGate — tier gating with hide, blur, lock, redirect modes
// NOT for: TierProvider logic or Stripe integration

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FeatureGate } from '../FeatureGate'
import { mockPush } from '@/__tests__/setup'

// WHY: Mock useTier to control tier state per test
const mockUseTier = vi.fn()
vi.mock('@/lib/hooks/useTier', () => ({
  useTier: () => mockUseTier(),
}))

describe('FeatureGate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when user has premium tier', () => {
    mockUseTier.mockReturnValue({ tier: 'premium' })

    render(
      <FeatureGate mode="hide">
        <div>Premium Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Premium Content')).toBeInTheDocument()
  })

  it('hides content for free tier in hide mode', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="hide">
        <div>Hidden Content</div>
      </FeatureGate>
    )
    expect(screen.queryByText('Hidden Content')).not.toBeInTheDocument()
  })

  it('shows fallback in hide mode when provided', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="hide" fallback={<div>Upgrade Please</div>}>
        <div>Hidden</div>
      </FeatureGate>
    )
    expect(screen.getByText('Upgrade Please')).toBeInTheDocument()
    expect(screen.queryByText('Hidden')).not.toBeInTheDocument()
  })

  it('renders blurred content with lock icon in blur mode', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="blur">
        <div>Blurred Content</div>
      </FeatureGate>
    )
    // WHY: Content is present but blurred via CSS
    expect(screen.getByText('Blurred Content')).toBeInTheDocument()
    expect(screen.getByText('Premium')).toBeInTheDocument()
  })

  it('shows lock message in lock mode', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="lock">
        <div>Locked</div>
      </FeatureGate>
    )
    expect(screen.getByText('Dostepne w Premium')).toBeInTheDocument()
    expect(screen.queryByText('Locked')).not.toBeInTheDocument()
  })

  it('redirects in redirect mode for free tier', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="redirect" redirectTo="/upgrade">
        <div>Gated</div>
      </FeatureGate>
    )
    expect(mockPush).toHaveBeenCalledWith('/upgrade')
  })

  it('uses default redirectTo when not specified', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="redirect">
        <div>Gated</div>
      </FeatureGate>
    )
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('allows access when requiredTier matches user tier', () => {
    mockUseTier.mockReturnValue({ tier: 'free' })

    render(
      <FeatureGate mode="hide" requiredTier="free">
        <div>Free Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Free Content')).toBeInTheDocument()
  })
})
