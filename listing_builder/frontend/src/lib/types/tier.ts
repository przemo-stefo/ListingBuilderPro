// frontend/src/lib/types/tier.ts
// Purpose: Tier system types for license-key based premium gating
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
  unlockPremium: (key?: string) => void
  isPremium: boolean
  licenseKey: string
  // WHY: true until localStorage is read on client — prevents FREE flash on refresh
  isLoading: boolean
}

// WHY: Daily limit for free tier
export const FREE_DAILY_LIMIT = 3
