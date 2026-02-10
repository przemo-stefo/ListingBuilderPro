// frontend/src/lib/types/tier.ts
// Purpose: Tier system types for Decoy Offer (free vs premium gating)
// NOT for: Backend tier enforcement or payment logic

export type TierLevel = 'free' | 'premium'

export type GatedFeature =
  | 'optimizer'
  | 'rag_knowledge'
  | 'keyword_intel'
  | 'monitoring'
  | 'history'
  | 'csv_export'
  | 'marketplace_all'
  | 'ranking_breakdown'

export type GateMode = 'hide' | 'blur' | 'lock' | 'redirect'

export interface TierContext {
  tier: TierLevel
  usageToday: number
  canOptimize: () => boolean
  incrementUsage: () => void
  unlockPremium: () => void
  isPremium: boolean
}

// WHY: Daily limit for free tier — Hormozi decoy strategy
export const FREE_DAILY_LIMIT = 3
