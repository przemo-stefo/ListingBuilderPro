// frontend/src/components/ui/WelcomeModal.tsx
// Purpose: First-run welcome dialog when user has 0 products
// NOT for: Returning users who dismissed or already imported

'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Upload, Sparkles, Send, X, ArrowRight } from 'lucide-react'
import { useLocalStorage } from '@/lib/hooks/useLocalStorage'

interface WelcomeModalProps {
  totalProducts: number
}

export function WelcomeModal({ totalProducts }: WelcomeModalProps) {
  const [dismissed, setDismissed] = useLocalStorage('lbp_welcome_dismissed', false)
  // WHY: Prevent flash — only show after hydration confirms localStorage is empty
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const dismiss = useCallback(() => setDismissed(true), [setDismissed])

  // WHY: ESC key closes modal — standard a11y pattern
  useEffect(() => {
    if (!mounted || dismissed || totalProducts > 0) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') dismiss()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [mounted, dismissed, totalProducts, dismiss])

  if (!mounted || dismissed || totalProducts > 0) return null

  const steps = [
    { icon: Upload, label: 'Import', desc: 'Zaimportuj produkty z Allegro, CSV lub ręcznie' },
    { icon: Sparkles, label: 'Optymalizacja', desc: 'AI generuje tytuł, bullety, opis i keywords' },
    { icon: Send, label: 'Eksport', desc: 'Wyeksportuj na Amazon, eBay, Kaufland' },
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={dismiss}
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
    >
      {/* WHY: stopPropagation prevents click-inside from triggering backdrop dismiss */}
      <div className="relative mx-4 w-full max-w-lg rounded-2xl border border-gray-800 bg-[#121212] p-8" onClick={e => e.stopPropagation()}>
        <button
          onClick={dismiss}
          aria-label="Zamknij"
          className="absolute right-4 top-4 text-gray-500 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <h2 id="welcome-modal-title" className="text-2xl font-bold text-white mb-2">Witaj w OctoHelper!</h2>
        <p className="text-gray-400 mb-6">3 kroki do profesjonalnych listingów na marketplace</p>

        <div className="space-y-4 mb-8">
          {steps.map((step, i) => {
            const Icon = step.icon
            return (
              <div key={step.label} className="flex items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/10">
                  <Icon className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{step.label}</p>
                  <p className="text-xs text-gray-500">{step.desc}</p>
                </div>
                {i < steps.length - 1 && (
                  <ArrowRight className="h-4 w-4 text-gray-600 shrink-0" />
                )}
              </div>
            )
          })}
        </div>

        <div className="flex gap-3">
          <Link
            href="/products/import"
            onClick={dismiss}
            className="flex-1 rounded-lg bg-white px-4 py-2.5 text-center text-sm font-medium text-black hover:bg-gray-200 transition-colors"
          >
            Zacznij importować
          </Link>
          <button
            onClick={dismiss}
            className="rounded-lg border border-gray-700 px-4 py-2.5 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Później
          </button>
        </div>
      </div>
    </div>
  )
}
