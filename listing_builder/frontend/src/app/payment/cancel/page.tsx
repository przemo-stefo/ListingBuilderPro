// frontend/src/app/payment/cancel/page.tsx
// Purpose: Payment cancelled page — simple redirect back to landing
// NOT for: Payment processing

'use client'

import { useRouter } from 'next/navigation'
import { XCircle, ArrowLeft } from 'lucide-react'

export default function PaymentCancelPage() {
  const router = useRouter()

  return (
    <div className="max-w-lg mx-auto text-center space-y-6 pt-16">
      <XCircle className="h-12 w-12 text-gray-500 mx-auto" />
      <h1 className="text-2xl font-bold text-white">Platnosc anulowana</h1>
      <p className="text-gray-400">
        Nie zostales obciazony. Mozesz wrocic i sprobowac ponownie w dowolnym momencie.
      </p>
      <button
        onClick={() => router.push('/')}
        className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-6 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Wroc na strone glowna
      </button>
    </div>
  )
}
