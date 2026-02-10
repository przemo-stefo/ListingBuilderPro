// frontend/src/lib/hooks/useTier.ts
// Purpose: Convenience hook for tier context
// NOT for: Tier logic (that's in TierProvider)

'use client'

import { useContext } from 'react'
import { TierCtx } from '@/components/providers/TierProvider'

export function useTier() {
  return useContext(TierCtx)
}
