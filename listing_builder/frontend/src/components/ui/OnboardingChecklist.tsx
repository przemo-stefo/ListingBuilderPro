// frontend/src/components/ui/OnboardingChecklist.tsx
// Purpose: 4-step onboarding checklist with auto-detection of completed steps
// NOT for: Full onboarding wizard or settings

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Check, Link2, Upload, Sparkles, Send, X } from 'lucide-react'
import { useLocalStorage } from '@/lib/hooks/useLocalStorage'

interface OnboardingChecklistProps {
  totalProducts: number
  optimizedCount: number
  publishedCount: number
  // WHY: Passed from dashboard's /oauth/status call — no extra API call needed
  hasOAuth: boolean
}

export function OnboardingChecklist({ totalProducts, optimizedCount, publishedCount, hasOAuth }: OnboardingChecklistProps) {
  const [dismissed, setDismissed] = useLocalStorage('lbp_checklist_dismissed', false)
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const steps = [
    { label: 'Połącz Allegro', done: hasOAuth, href: '/integrations', icon: Link2 },
    { label: 'Importuj produkt', done: totalProducts > 0, href: '/products/import', icon: Upload },
    { label: 'Zoptymalizuj listing', done: optimizedCount > 0, href: '/optimize', icon: Sparkles },
    { label: 'Eksportuj na marketplace', done: publishedCount > 0, href: '/publish', icon: Send },
  ]

  const completedCount = steps.filter(s => s.done).length
  const allDone = completedCount === steps.length

  if (!mounted || dismissed || allDone) return null

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-white">Pierwsze kroki</h3>
          <p className="text-xs text-gray-500 mt-0.5">{completedCount}/{steps.length} kroków ukończonych</p>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-gray-600 hover:text-white transition-colors"
          aria-label="Zamknij checklist"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-800 rounded-full h-1.5 mb-4" role="progressbar" aria-valuenow={completedCount} aria-valuemin={0} aria-valuemax={steps.length}>
        <div
          className="bg-green-500 h-1.5 rounded-full transition-all"
          style={{ width: `${(completedCount / steps.length) * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {steps.map((step) => {
          const Icon = step.icon
          return (
            <Link
              key={step.label}
              href={step.href}
              className={`flex items-center gap-3 rounded-lg p-2.5 transition-colors ${
                step.done ? 'opacity-60' : 'hover:bg-white/5'
              }`}
            >
              <div className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 ${
                step.done ? 'bg-green-500/20 text-green-400' : 'bg-gray-800 text-gray-500'
              }`}>
                {step.done ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
              </div>
              <span className={`text-sm ${step.done ? 'text-gray-500 line-through' : 'text-white'}`}>
                {step.label}
              </span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
