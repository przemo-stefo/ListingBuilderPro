// frontend/src/components/tier/UpgradeCTA.tsx
// Purpose: Upgrade call-to-action — redirects to Stripe Checkout
// NOT for: Payment processing or license key management

'use client'

import { useState } from 'react'
import { Crown, Sparkles, ArrowRight } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import { cn } from '@/lib/utils'

interface UpgradeCTAProps {
  variant?: 'inline' | 'card'
  className?: string
}

async function redirectToCheckout(planType: 'lifetime' | 'monthly') {
  const email = prompt('Podaj email (do odzyskania klucza licencyjnego):')
  if (!email) return

  const res = await fetch('/api/proxy/stripe/create-checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan_type: planType, email }),
  })

  if (!res.ok) {
    alert('Blad tworzenia sesji platnosci. Sprobuj ponownie.')
    return
  }

  const data = await res.json()
  if (data.checkout_url) {
    window.location.href = data.checkout_url
  }
}

export function UpgradeCTA({ variant = 'inline', className }: UpgradeCTAProps) {
  const { isPremium } = useTier()
  const [loading, setLoading] = useState(false)

  if (isPremium) return null

  const handleUpgrade = async (plan: 'lifetime' | 'monthly') => {
    setLoading(true)
    try {
      await redirectToCheckout(plan)
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
          onClick={() => handleUpgrade('lifetime')}
          disabled={loading}
          className="flex items-center gap-1 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 transition-colors disabled:opacity-50"
        >
          <Sparkles className="h-3 w-3" />
          {loading ? 'Ladowanie...' : 'Upgrade — 149 PLN'}
          <ArrowRight className="h-3 w-3" />
        </button>
      </div>
    )
  }

  // Card variant — full comparison with both plans
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
      <div className="space-y-2">
        <button
          onClick={() => handleUpgrade('lifetime')}
          disabled={loading}
          className="w-full rounded-lg bg-amber-500 py-2.5 text-sm font-bold text-black hover:bg-amber-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Sparkles className="h-4 w-4" />
          {loading ? 'Ladowanie...' : '149 PLN — Lifetime'}
        </button>
        <button
          onClick={() => handleUpgrade('monthly')}
          disabled={loading}
          className="w-full rounded-lg border border-amber-500/30 bg-transparent py-2.5 text-sm font-medium text-amber-400 hover:bg-amber-500/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? 'Ladowanie...' : '49 PLN/mies'}
        </button>
      </div>
    </div>
  )
}
