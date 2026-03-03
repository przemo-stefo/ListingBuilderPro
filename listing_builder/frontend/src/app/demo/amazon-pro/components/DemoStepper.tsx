// frontend/src/app/demo/amazon-pro/components/DemoStepper.tsx
// Purpose: Horizontal 5-step stepper with labels and active state
// NOT for: Step content rendering (that's in Step*.tsx components)

'use client'

import { Check } from 'lucide-react'

interface Step {
  number: number
  label: string
  shortLabel: string
}

const STEPS: Step[] = [
  { number: 1, label: '1. Produkt', shortLabel: 'Fetch' },
  { number: 2, label: '2. AI Listing', shortLabel: 'Optimize' },
  { number: 3, label: '3. Compliance', shortLabel: 'Check' },
  { number: 4, label: '4. Publikacja', shortLabel: 'Publish' },
  { number: 5, label: '5. Kupon', shortLabel: 'Coupon' },
]

interface DemoStepperProps {
  currentStep: number
  completedSteps: number[]
}

export default function DemoStepper({ currentStep, completedSteps }: DemoStepperProps) {
  return (
    <div className="flex items-center justify-between w-full">
      {STEPS.map((step, idx) => {
        const isCompleted = completedSteps.includes(step.number)
        const isCurrent = currentStep === step.number
        const isPast = step.number < currentStep

        return (
          <div key={step.number} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center gap-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-colors ${
                  isCompleted
                    ? 'bg-green-600 border-green-600 text-white'
                    : isCurrent
                      ? 'bg-white/10 border-white text-white'
                      : 'bg-transparent border-gray-700 text-gray-500'
                }`}
              >
                {isCompleted ? <Check className="w-5 h-5" /> : step.number}
              </div>
              <span
                className={`text-xs whitespace-nowrap ${
                  isCurrent ? 'text-white font-medium' : isPast ? 'text-gray-400' : 'text-gray-600'
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {idx < STEPS.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-2 mt-[-1rem] ${
                  isPast || isCompleted ? 'bg-green-600' : 'bg-gray-700'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
