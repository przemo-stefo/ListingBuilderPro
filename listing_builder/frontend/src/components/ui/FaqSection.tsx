// frontend/src/components/ui/FaqSection.tsx
// Purpose: Reusable FAQ accordion — used across all tabs
// NOT for: Tab-specific content (pass items as props)

'use client'

import { useState } from 'react'
import { HelpCircle, ChevronDown, ChevronRight } from 'lucide-react'

interface FaqItemProps {
  question: string
  answer: string
}

export function FaqItem({ question, answer }: FaqItemProps) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-gray-800 bg-[#151515]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-gray-300">{question}</span>
        {open ? (
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-gray-500" />
        ) : (
          <ChevronRight className="ml-2 h-4 w-4 shrink-0 text-gray-500" />
        )}
      </button>
      {open && (
        <p className="px-4 pb-3 text-sm text-gray-500 leading-relaxed">{answer}</p>
      )}
    </div>
  )
}

interface FaqSectionProps {
  title: string
  subtitle?: string
  items: FaqItemProps[]
}

export function FaqSection({ title, subtitle, items }: FaqSectionProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between p-5"
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-gray-400" />
          <div className="text-left">
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
          </div>
        </div>
        {open ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>
      {open && (
        <div className="space-y-3 px-5 pb-5">
          {items.map((item, i) => (
            <FaqItem key={i} question={item.question} answer={item.answer} />
          ))}
        </div>
      )}
    </div>
  )
}
