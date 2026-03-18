// frontend/src/app/validator/components/score-utils.ts
// Purpose: Shared score color/styling helpers for validator components
// NOT for: Business logic or API calls

export function scoreColor(score: number): string {
  if (score >= 8) return 'text-green-400'
  if (score >= 6) return 'text-amber-400'
  return 'text-red-400'
}

export function scoreBg(score: number): string {
  if (score >= 8) return 'bg-green-900/20 border-green-800'
  if (score >= 6) return 'bg-amber-900/20 border-amber-800'
  return 'bg-red-900/20 border-red-800'
}
