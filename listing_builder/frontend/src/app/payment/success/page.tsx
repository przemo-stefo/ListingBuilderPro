// frontend/src/app/payment/success/page.tsx
// Purpose: Post-payment page — polls for license key, saves to localStorage, redirects
// NOT for: Payment processing (that's backend)

'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckCircle, Loader2, Copy, Check } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'

function SuccessContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { unlockPremium } = useTier()
  const [licenseKey, setLicenseKey] = useState<string | null>(null)
  const [status, setStatus] = useState<'polling' | 'ready' | 'error'>('polling')
  const [copied, setCopied] = useState(false)

  const sessionId = searchParams.get('session_id')

  useEffect(() => {
    if (!sessionId) {
      setStatus('error')
      return
    }

    let attempts = 0
    const maxAttempts = 20

    // WHY: Webhook may arrive after redirect — poll until license key appears
    const poll = async () => {
      try {
        const res = await fetch(`/api/proxy/stripe/session/${sessionId}/license`)
        if (!res.ok) throw new Error('fetch failed')

        const data = await res.json()
        if (data.status === 'ready' && data.license_key) {
          setLicenseKey(data.license_key)
          setStatus('ready')
          unlockPremium(data.license_key)
          return
        }

        attempts++
        if (attempts >= maxAttempts) {
          setStatus('error')
          return
        }

        setTimeout(poll, 2000)
      } catch {
        attempts++
        if (attempts >= maxAttempts) {
          setStatus('error')
          return
        }
        setTimeout(poll, 2000)
      }
    }

    poll()
  }, [sessionId, unlockPremium])

  const handleCopy = () => {
    if (licenseKey) {
      navigator.clipboard.writeText(licenseKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="max-w-lg mx-auto text-center space-y-6 pt-16">
      {status === 'polling' && (
        <>
          <Loader2 className="h-12 w-12 text-amber-400 animate-spin mx-auto" />
          <h1 className="text-2xl font-bold text-white">Przetwarzanie płatności...</h1>
          <p className="text-gray-400">Czekam na potwierdzenie od Stripe. To może zająć kilka sekund.</p>
        </>
      )}

      {status === 'ready' && licenseKey && (
        <>
          <CheckCircle className="h-12 w-12 text-green-400 mx-auto" />
          <h1 className="text-2xl font-bold text-white">Premium aktywny!</h1>
          <p className="text-gray-400">Twój klucz licencyjny (zachowaj go!):</p>

          <div className="flex items-center gap-2 bg-[#121212] border border-gray-700 rounded-lg p-3">
            <code className="flex-1 text-sm text-amber-400 break-all text-left">{licenseKey}</code>
            <button onClick={handleCopy} className="shrink-0 p-2 hover:bg-gray-800 rounded">
              {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-gray-400" />}
            </button>
          </div>

          <p className="text-xs text-gray-500">
            Klucz został zapisany automatycznie. Możesz go odzyskać w każdej chwili podając email.
          </p>

          <button
            onClick={() => router.push('/dashboard')}
            className="w-full rounded-lg bg-amber-500 py-3 text-sm font-bold text-black hover:bg-amber-400 transition-colors"
          >
            Przejdź do Dashboard
          </button>
        </>
      )}

      {status === 'error' && (
        <>
          <div className="h-12 w-12 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto">
            <span className="text-2xl">!</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Coś poszło nie tak</h1>
          <p className="text-gray-400">
            Płatność została przetworzona, ale nie udało się pobrać klucza.
            Użyj opcji odzyskiwania klucza na stronie głównej.
          </p>
          <button
            onClick={() => router.push('/payment/recover')}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors"
          >
            Odzyskaj klucz
          </button>
        </>
      )}
    </div>
  )
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="max-w-lg mx-auto text-center pt-16">
        <Loader2 className="h-12 w-12 text-amber-400 animate-spin mx-auto" />
      </div>
    }>
      <SuccessContent />
    </Suspense>
  )
}
