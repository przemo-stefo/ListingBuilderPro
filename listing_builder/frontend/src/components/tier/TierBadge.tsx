// frontend/src/components/tier/TierBadge.tsx
// Purpose: Visual badge showing current tier level
// NOT for: Tier logic or gating

import { Crown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TierLevel } from '@/lib/types/tier'

interface TierBadgeProps {
  tier: TierLevel
  className?: string
  size?: 'sm' | 'md'
}

export function TierBadge({ tier, className, size = 'sm' }: TierBadgeProps) {
  const isPremium = tier === 'premium'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs',
        isPremium
          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
          : 'bg-gray-500/10 text-gray-400 border border-gray-700',
        className
      )}
    >
      {isPremium && <Crown className={size === 'sm' ? 'h-2.5 w-2.5' : 'h-3 w-3'} />}
      {isPremium ? 'PREMIUM' : 'FREE'}
    </span>
  )
}
