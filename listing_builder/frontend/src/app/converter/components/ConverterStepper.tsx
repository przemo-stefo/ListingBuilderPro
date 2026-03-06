// frontend/src/app/converter/components/ConverterStepper.tsx
// Purpose: Step indicator for converter wizard — visual progress bar
// NOT for: Step content (that's in page.tsx)

import { CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const STEPS = [
  { label: 'Produkty' },
  { label: 'Marketplace' },
  { label: 'Ustawienia' },
  { label: 'Wyniki' },
]

interface ConverterStepperProps {
  currentStep: number
  completedSteps: Set<number>
  onStepClick: (step: number) => void
}

export function ConverterStepper({ currentStep, completedSteps, onStepClick }: ConverterStepperProps) {
  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, i) => {
        const isCompleted = completedSteps.has(i)
        const isCurrent = currentStep === i
        // WHY: Can only click completed steps or the next step after last completed
        const canClick = isCompleted || i <= Math.max(...Array.from(completedSteps), -1) + 1

        return (
          <div key={i} className="flex items-center gap-2">
            {i > 0 && (
              <div className={cn('h-px w-6', isCompleted ? 'bg-white' : 'bg-gray-700')} />
            )}
            <button
              onClick={() => canClick && onStepClick(i)}
              disabled={!canClick}
              className={cn(
                'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
                isCurrent && 'bg-white text-black',
                isCompleted && !isCurrent && 'bg-white/10 text-white hover:bg-white/20',
                !isCurrent && !isCompleted && 'text-gray-500',
                !canClick && 'cursor-not-allowed opacity-50',
              )}
            >
              {isCompleted ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <span className={cn(
                  'flex h-4 w-4 items-center justify-center rounded-full text-[10px]',
                  isCurrent ? 'bg-black text-white' : 'border border-gray-600 text-gray-500'
                )}>
                  {i + 1}
                </span>
              )}
              {step.label}
            </button>
          </div>
        )
      })}
    </div>
  )
}
