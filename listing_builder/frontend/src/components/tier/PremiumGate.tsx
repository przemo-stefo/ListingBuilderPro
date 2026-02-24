// frontend/src/components/tier/PremiumGate.tsx
// Purpose: Wrapper that shows upgrade CTA for free-tier users on premium pages
// NOT for: Feature-level gating (that's handled inline with useTier)

'use client'

import Link from 'next/link'
import { Crown, ArrowRight } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import type { ReactNode } from 'react'

interface PremiumGateProps {
  children: ReactNode
  feature: string
}

export function PremiumGate({ children, feature }: PremiumGateProps) {
  const { isPremium, isLoading } = useTier()

  // WHY: Don't flash the gate while tier is loading
  if (isLoading) return null

  if (isPremium) return <>{children}</>

  return (
    <div className="flex flex-col items-center justify-center py-20 space-y-6">
      <div className="rounded-2xl bg-amber-500/10 border border-amber-500/20 p-6">
        <Crown className="h-12 w-12 text-amber-400 mx-auto" />
      </div>
      <div className="text-center space-y-2 max-w-md">
        <h2 className="text-xl font-bold text-white">{feature} — Premium</h2>
        <p className="text-sm text-gray-400">
          Ta funkcja jest dostępna w planie Premium. Uaktualnij konto, żeby odblokować pełne możliwości.
        </p>
      </div>
      <Link
        href="/account?upgrade=1"
        className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-6 py-3 text-sm font-semibold text-black hover:bg-amber-400 transition-colors"
      >
        Uaktualnij do Premium
        <ArrowRight className="h-4 w-4" />
      </Link>
      <p className="text-xs text-gray-600">49 PLN/miesiąc · Promo 39 PLN</p>
    </div>
  )
}
