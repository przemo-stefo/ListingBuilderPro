// frontend/src/components/tier/UpgradeCTA.tsx
// Purpose: Upgrade call-to-action — redirects to Stripe Checkout (monthly only)
// NOT for: Payment processing or license key management

'use client'

import { useState } from 'react'
import { Crown, Sparkles, ArrowRight } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import { useAuth } from '@/components/providers/AuthProvider'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'
import { safeRedirect } from '@/lib/utils/redirect'

interface UpgradeCTAProps {
  variant?: 'inline' | 'card'
  className?: string
}

export function UpgradeCTA({ variant = 'inline', className }: UpgradeCTAProps) {
  const { isPremium } = useTier()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)

  if (isPremium) return null

  const handleUpgrade = async () => {
    // WHY: Use logged-in user's email; fallback to prompt for unauthenticated views
    const email = user?.email || prompt('Podaj email (do odzyskania klucza licencyjnego):')
    if (!email) return
    setLoading(true)
    try {
      const { data } = await apiClient.post('/stripe/create-checkout', {
        plan_type: 'monthly', email,
      })
      if (data.checkout_url) {
        safeRedirect(data.checkout_url)
      }
    } catch {
      alert('Błąd tworzenia sesji płatności. Spróbuj ponownie.')
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
          {loading ? 'Ladowanie...' : '19,00 PLN/mies'}
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
          <span className="text-amber-400">+</span> Optymalizator AI — bez limitów, wszystkie marketplace
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Import produktów z URL, CSV i Allegro
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Konwerter ofert między platformami
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Listing Score — ocena listingu AI
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Walidator Produktu — analiza potencjału
        </li>
        <li className="flex items-center gap-2">
          <span className="text-amber-400">+</span> Ekspert Kaufland — AI chatbot z bazą wiedzy
        </li>
      </ul>
      <button
        onClick={handleUpgrade}
        disabled={loading}
        className="w-full rounded-lg bg-amber-500 py-2.5 text-sm font-bold text-black hover:bg-amber-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <Sparkles className="h-4 w-4" />
        {loading ? 'Ladowanie...' : '19,00 PLN / miesiac'}
      </button>
    </div>
  )
}
