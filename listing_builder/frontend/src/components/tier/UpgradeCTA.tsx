// frontend/src/components/tier/UpgradeCTA.tsx
// Purpose: Upgrade call-to-action — redirects to Stripe Checkout (monthly only)
// NOT for: Payment processing or license key management

'use client'

import { useState } from 'react'
import { Crown, Sparkles, ArrowRight } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'
import { safeRedirect } from '@/lib/utils/redirect'

interface UpgradeCTAProps {
  variant?: 'inline' | 'card'
  className?: string
}

async function redirectToCheckout() {
  const email = prompt('Podaj email (do odzyskania klucza licencyjnego):')
  if (!email) return

  try {
    // WHY: apiClient sends JWT + License-Key (raw fetch() was missing them)
    const { data } = await apiClient.post('/stripe/create-checkout', {
      plan_type: 'monthly', email,
    })
    if (data.checkout_url) {
      safeRedirect(data.checkout_url)
    }
  } catch {
    alert('Blad tworzenia sesji platnosci. Sprobuj ponownie.')
  }
}

export function UpgradeCTA({ variant = 'inline', className }: UpgradeCTAProps) {
  const { isPremium } = useTier()
  const [loading, setLoading] = useState(false)

  if (isPremium) return null

  const handleUpgrade = async () => {
    setLoading(true)
    try {
      await redirectToCheckout()
    } finally {
      setLoading(false)
    }
  }

  if (variant === 'inline') {
    return (
      <div
        className={cn(
          'flex items-center justify-between rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3',
          className
        )}
      >
        <div className="flex items-center gap-2">
          <Crown className="h-4 w-4 text-amber-400" />
          <span className="text-sm text-gray-300">
            Odblokuj pelny dostep do wszystkich funkcji
          </span>
        </div>
        <button
          onClick={handleUpgrade}
          disabled={loading}
          className="flex items-center gap-1 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 transition-colors disabled:opacity-50"
        >
          <Sparkles className="h-3 w-3" />
          {loading ? 'Ladowanie...' : '49 PLN/mies'}
          <ArrowRight className="h-3 w-3" />
        </button>
      </div>
    )
  }

  // Card variant — feature list + single monthly plan
  return (
    <div
      className={cn(
        'rounded-xl border border-amber-500/30 bg-gradient-to-b from-amber-500/5 to-transparent p-6',
        className
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <Crown className="h-5 w-5 text-amber-400" />
        <h3 className="text-lg font-bold text-white">Premium</h3>
      </div>
      <ul className="space-y-2 mb-4 text-sm text-gray-300">
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Nieograniczone optymalizacje
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> RAG Knowledge Base
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Keyword Intelligence
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Monitoring & Alerty
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Historia + CSV Export
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Wszystkie marketplace&apos;y
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Ranking Juice breakdown
        </li>
      </ul>
      <button
        onClick={handleUpgrade}
        disabled={loading}
        className="w-full rounded-lg bg-amber-500 py-2.5 text-sm font-bold text-black hover:bg-amber-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <Sparkles className="h-4 w-4" />
        {loading ? 'Ladowanie...' : '49 PLN / miesiac'}
      </button>
    </div>
  )
}
