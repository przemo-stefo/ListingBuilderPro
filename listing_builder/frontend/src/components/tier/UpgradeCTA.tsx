// frontend/src/components/tier/UpgradeCTA.tsx
// Purpose: Upgrade call-to-action — inline banner or full comparison card
// NOT for: Payment processing or auth

'use client'

import { Crown, Sparkles, ArrowRight } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import { cn } from '@/lib/utils'

interface UpgradeCTAProps {
  variant?: 'inline' | 'card'
  className?: string
}

export function UpgradeCTA({ variant = 'inline', className }: UpgradeCTAProps) {
  const { unlockPremium, isPremium } = useTier()

  if (isPremium) return null

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
          onClick={unlockPremium}
          className="flex items-center gap-1 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 transition-colors"
        >
          <Sparkles className="h-3 w-3" />
          Upgrade
          <ArrowRight className="h-3 w-3" />
        </button>
      </div>
    )
  }

  // Card variant — full comparison
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
        onClick={unlockPremium}
        className="w-full rounded-lg bg-amber-500 py-2.5 text-sm font-bold text-black hover:bg-amber-400 transition-colors flex items-center justify-center gap-2"
      >
        <Sparkles className="h-4 w-4" />
        Odblokuj pelna moc
      </button>
    </div>
  )
}
