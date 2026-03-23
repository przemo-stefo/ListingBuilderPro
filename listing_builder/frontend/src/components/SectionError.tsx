// frontend/src/components/SectionError.tsx
// Purpose: Reusable error boundary UI for app sections
// NOT for: API-level error display (handled per-component)

'use client'

import { useEffect } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'

interface SectionErrorProps {
  error: Error & { digest?: string }
  reset: () => void
  sectionName: string
}

export default function SectionError({ error, reset, sectionName }: SectionErrorProps) {
  useEffect(() => {
    console.error(`${sectionName} error:`, error)
  }, [error, sectionName])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-4">
      <AlertTriangle className="h-12 w-12 text-red-400" />
      <div className="text-center">
        <h2 className="text-lg font-semibold text-white">{sectionName} napotkał problem</h2>
        <p className="mt-2 text-sm text-gray-400">
          Nie udało się załadować modułu. Spróbuj ponownie.
        </p>
      </div>
      <button
        onClick={reset}
        className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/15 transition-colors"
      >
        <RotateCcw className="h-4 w-4" />
        Spróbuj ponownie
      </button>
    </div>
  )
}
