// frontend/src/app/error.tsx
// Purpose: Global error boundary — catches unhandled runtime errors in any page
// NOT for: 404 pages (that's not-found.tsx) or API errors (handled per-component)

'use client'

import { useEffect } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // WHY: Log to console so developers can debug — never send error.message to backend
    console.error('Unhandled error:', error)
  }, [error])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-4">
      <AlertTriangle className="h-12 w-12 text-red-400" />
      <div className="text-center">
        <h2 className="text-lg font-semibold text-white">Coś poszło nie tak</h2>
        <p className="mt-2 text-sm text-gray-400">
          Wystąpił nieoczekiwany błąd. Spróbuj odświeżyć stronę.
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
