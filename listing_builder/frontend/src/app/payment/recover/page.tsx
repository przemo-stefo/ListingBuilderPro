// frontend/src/app/payment/recover/page.tsx
// Purpose: License key recovery by email
// NOT for: Payment processing

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { KeyRound, Copy, Check, ArrowLeft, LogIn } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'
import { useAuth } from '@/components/providers/AuthProvider'
import { apiClient } from '@/lib/api/client'

export default function RecoverLicensePage() {
  const router = useRouter()
  const { unlockPremium } = useTier()
  const { user, session, loading: authLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [licenseKey, setLicenseKey] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  // WHY: Backend requires JWT — user must be logged in to recover their own key
  if (!authLoading && !user) {
    return (
      <div className="max-w-lg mx-auto space-y-6 pt-16 text-center">
        <KeyRound className="h-10 w-10 text-amber-400 mx-auto" />
        <h1 className="text-2xl font-bold text-white">Odzyskaj klucz licencyjny</h1>
        <p className="text-gray-400 text-sm">Zaloguj się, aby odzyskać swój klucz</p>
        <button
          onClick={() => router.push('/login?next=/payment/recover')}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-6 py-3 text-sm font-bold text-black hover:bg-amber-400 transition-colors"
        >
          <LogIn className="h-4 w-4" />
          Zaloguj się
        </button>
      </div>
    )
  }

  const handleRecover = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLicenseKey(null)
    setLoading(true)

    try {
      // WHY: apiClient sends JWT automatically (no manual Authorization header needed)
      const { data } = await apiClient.post('/stripe/recover-license', {
        email: email || user?.email,
      })
      if (data.found && data.license_key) {
        setLicenseKey(data.license_key)
        unlockPremium(data.license_key)
      } else {
        setError('Nie znaleziono aktywnej licencji dla tego adresu email.')
      }
    } catch {
      setError('Błąd połączenia. Spróbuj ponownie.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (licenseKey) {
      navigator.clipboard.writeText(licenseKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 pt-16">
      <div className="text-center space-y-2">
        <KeyRound className="h-10 w-10 text-amber-400 mx-auto" />
        <h1 className="text-2xl font-bold text-white">Odzyskaj klucz licencyjny</h1>
        <p className="text-gray-400 text-sm">Klucz zostanie odzyskany dla Twojego konta</p>
      </div>

      <form onSubmit={handleRecover} className="space-y-4">
        <input
          type="email"
          value={email || user?.email || ''}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email@example.com"
          disabled
          className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !(email || user?.email)}
          className="w-full rounded-lg bg-amber-500 py-3 text-sm font-bold text-black hover:bg-amber-400 transition-colors disabled:opacity-50"
        >
          {loading ? 'Szukam...' : 'Odzyskaj klucz'}
        </button>
      </form>

      {error && (
        <p className="text-red-400 text-sm text-center">{error}</p>
      )}

      {licenseKey && (
        <div className="space-y-3">
          <p className="text-green-400 text-sm text-center">Znaleziono! Klucz został aktywowany.</p>
          <div className="flex items-center gap-2 bg-[#121212] border border-gray-700 rounded-lg p-3">
            <code className="flex-1 text-sm text-amber-400 break-all">{licenseKey}</code>
            <button onClick={handleCopy} className="shrink-0 p-2 hover:bg-gray-800 rounded">
              {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-gray-400" />}
            </button>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full rounded-lg bg-amber-500 py-2.5 text-sm font-bold text-black hover:bg-amber-400 transition-colors"
          >
            Przejdź do Dashboard
          </button>
        </div>
      )}

      <div className="text-center">
        <button
          onClick={() => router.push('/')}
          className="inline-flex items-center gap-1 text-gray-500 text-xs hover:text-gray-400 transition-colors"
        >
          <ArrowLeft className="h-3 w-3" />
          Wróć na stronę główną
        </button>
      </div>
    </div>
  )
}
