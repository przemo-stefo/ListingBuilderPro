// frontend/src/components/ui/FlowIndicator.tsx
// Purpose: Reusable 3-step flow stepper (Import → Optymalizacja → Eksport)
// NOT for: Navigation logic or data fetching

'use client'

import Link from 'next/link'
import { ArrowRight, Check } from 'lucide-react'
import { formatNumber } from '@/lib/utils'

interface FlowIndicatorProps {
  stats: {
    total_products?: number
    pending_optimization?: number
    optimized_products?: number
  } | null
  currentStep?: 'import' | 'optimize' | 'export'
}

export function FlowIndicator({ stats, currentStep }: FlowIndicatorProps) {
  const totalProducts = stats?.total_products || 0
  const pendingCount = stats?.pending_optimization || 0
  const optimizedCount = stats?.optimized_products || 0

  const steps = [
    {
      key: 'import' as const,
      href: '/products/import',
      label: 'Import',
      sublabel: totalProducts > 0 ? `${formatNumber(totalProducts)} produktów` : 'Zacznij tutaj',
      done: totalProducts > 0,
      active: pendingCount === 0 && optimizedCount === 0 && totalProducts === 0,
    },
    {
      key: 'optimize' as const,
      href: '/optimize',
      label: 'Optymalizacja',
      sublabel: pendingCount > 0 ? `${pendingCount} czeka` : optimizedCount > 0 ? `${optimizedCount} gotowych` : 'Brak produktów',
      done: optimizedCount > 0 && pendingCount === 0,
      active: pendingCount > 0,
    },
    {
      key: 'export' as const,
      href: '/publish',
      label: 'Eksport',
      sublabel: optimizedCount > 0 ? `${optimizedCount} do eksportu` : 'Brak gotowych',
      done: false,
      active: false,
    },
  ]

  return (
    <div className="flex items-stretch rounded-xl border border-gray-800 bg-[#1A1A1A] p-3 gap-1">
      {steps.map((step, i) => {
        const isCurrent = currentStep === step.key
        return (
          <div key={step.key} className="flex flex-1 items-center">
            <Link
              href={step.href}
              className={`flex flex-1 items-center gap-3 rounded-lg p-3 hover:bg-white/5 transition-colors ${
                isCurrent ? 'bg-white/5 border border-white/20' : ''
              }`}
            >
              <div className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                step.done ? 'bg-green-500/20 text-green-400' :
                isCurrent ? 'bg-white/10 text-white ring-2 ring-white/20' :
                step.active ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-gray-800 text-gray-500'
              }`}>
                {step.done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              <div>
                <p className="text-sm font-medium text-white">{step.label}</p>
                <p className="text-xs text-gray-500">{step.sublabel}</p>
              </div>
            </Link>
            {i < steps.length - 1 && (
              <div className="flex items-center px-1">
                <ArrowRight className="h-4 w-4 text-gray-600" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
