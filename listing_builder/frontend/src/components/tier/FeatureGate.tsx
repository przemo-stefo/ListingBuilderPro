// frontend/src/components/tier/FeatureGate.tsx
// Purpose: Conditional renderer that gates features based on user tier
// NOT for: Business logic or tier persistence

'use client'

import { useRouter } from 'next/navigation'
import { Lock } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import type { TierLevel, GateMode } from '@/lib/types/tier'
import type { ReactNode } from 'react'

interface FeatureGateProps {
  requiredTier?: TierLevel
  mode: GateMode
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

export function FeatureGate({
  requiredTier = 'premium',
  mode,
  children,
  fallback,
  redirectTo = '/',
}: FeatureGateProps) {
  const { tier } = useTier()
  const router = useRouter()

  const hasAccess = tier === 'premium' || tier === requiredTier

  if (hasAccess) return <>{children}</>

  switch (mode) {
    case 'hide':
      return fallback ? <>{fallback}</> : null

    case 'blur':
      return (
        <div className="relative">
          <div className="pointer-events-none select-none blur-sm">{children}</div>
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-lg">
            <div className="flex flex-col items-center gap-2">
              <Lock className="h-6 w-6 text-amber-400" />
              <span className="text-sm font-medium text-amber-400">Premium</span>
            </div>
          </div>
        </div>
      )

    case 'lock':
      return (
        <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-500/5 px-4 py-3">
          <Lock className="h-4 w-4 text-amber-400" />
          <span className="text-sm text-gray-400">Dostepne w Premium</span>
        </div>
      )

    case 'redirect':
      // WHY: Push to landing on mount if not premium
      if (typeof window !== 'undefined') {
        router.push(redirectTo)
      }
      return null

    default:
      return <>{children}</>
  }
}
