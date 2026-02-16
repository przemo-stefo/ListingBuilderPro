// frontend/src/app/page.tsx
// Purpose: Landing page with pricing — FREE vs PREMIUM with Stripe checkout
// NOT for: Dashboard stats or app functionality (that's /dashboard)

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Crown, Sparkles, Check, X, ArrowRight, Zap } from 'lucide-react'
import { useTier } from '@/lib/hooks/useTier'

const FREE_FEATURES = [
  { label: '3 optymalizacje dziennie', included: true },
  { label: 'Amazon tylko', included: true },
  { label: 'Ranking Juice (sam wynik)', included: true },
  { label: 'RAG Knowledge Base', included: false },
  { label: 'Keyword Intelligence', included: false },
  { label: 'Monitoring & Alerty', included: false },
  { label: 'Historia optymalizacji', included: false },
  { label: 'CSV Export', included: false },
  { label: 'Wszystkie marketplace\'y', included: false },
  { label: 'Ranking Juice breakdown', included: false },
]

const PREMIUM_FEATURES = [
  { label: 'Nieograniczone optymalizacje', included: true },
  { label: 'Wszystkie marketplace\'y', included: true },
  { label: 'Ranking Juice + full breakdown', included: true },
  { label: 'RAG Knowledge Base', included: true },
  { label: 'Keyword Intelligence', included: true },
  { label: 'Monitoring & Alerty', included: true },
  { label: 'Historia optymalizacji', included: true },
  { label: 'CSV Export', included: true },
  { label: 'Expert Q&A', included: true },
  { label: 'Priorytetowe wsparcie', included: true },
]

async function redirectToCheckout() {
  const email = prompt('Podaj email (do odzyskania klucza licencyjnego):')
  if (!email) return

  const res = await fetch('/api/proxy/stripe/create-checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan_type: 'monthly', email }),
  })

  if (!res.ok) {
    alert('Blad tworzenia sesji platnosci. Sprobuj ponownie.')
    return
  }

  const data = await res.json()
  if (data.checkout_url) {
    window.location.href = data.checkout_url
  }
}

export default function LandingPage() {
  const router = useRouter()
  const { isPremium } = useTier()
  const [loading, setLoading] = useState(false)

  const handleFreeStart = () => {
    router.push('/optimize')
  }

  const handlePremiumStart = async () => {
    setLoading(true)
    try {
      await redirectToCheckout()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-12">
      {/* Hero */}
      <div className="text-center space-y-4 pt-8">
        <h1 className="text-4xl font-bold text-white">
          <span className="text-amber-400">Octosello</span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Asystent sprzedawcy marketplace. Optymalizuj listingi AI, konwertuj oferty Allegro
          na Amazon/eBay/Kaufland i monitoruj compliance — wszystko w jednym panelu.
        </p>
      </div>

      {/* Side-by-side cards */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* FREE card — smaller, muted (40%) */}
        <div className="md:col-span-5 rounded-xl border border-gray-800 bg-[#121212] p-6 flex flex-col">
          <div className="mb-6">
            <span className="inline-flex items-center gap-1 rounded-full bg-gray-500/10 border border-gray-700 px-3 py-1 text-xs font-medium text-gray-400">
              FREE
            </span>
            <h2 className="text-2xl font-bold text-gray-300 mt-3">Zacznij za darmo</h2>
            <p className="text-sm text-gray-500 mt-1">Sprawdz mozliwosci platformy</p>
          </div>

          <ul className="space-y-3 flex-1">
            {FREE_FEATURES.map((f) => (
              <li key={f.label} className="flex items-center gap-2 text-sm">
                {f.included ? (
                  <Check className="h-4 w-4 text-gray-500 shrink-0" />
                ) : (
                  <X className="h-4 w-4 text-gray-700 shrink-0" />
                )}
                <span className={f.included ? 'text-gray-400' : 'text-gray-600'}>
                  {f.label}
                </span>
              </li>
            ))}
          </ul>

          <button
            onClick={handleFreeStart}
            className="mt-6 w-full rounded-lg border border-gray-700 bg-gray-800 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
          >
            Zacznij za darmo
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* PREMIUM card — larger, golden accent (60%) */}
        <div className="md:col-span-7 rounded-xl border border-amber-500/30 bg-gradient-to-b from-amber-500/5 to-[#121212] p-6 flex flex-col relative overflow-hidden">
          {/* Glow effect */}
          <div className="absolute -top-24 -right-24 h-48 w-48 rounded-full bg-amber-500/10 blur-3xl" />

          <div className="mb-6 relative">
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/30 px-3 py-1 text-xs font-medium text-amber-400">
              <Crown className="h-3 w-3" />
              PREMIUM
            </span>
            <h2 className="text-3xl font-bold text-white mt-3">Pelna moc AI</h2>
            <p className="text-sm text-gray-400 mt-1">Wszystko czego potrzebujesz do dominacji rynku</p>
          </div>

          <ul className="space-y-3 flex-1 relative">
            {PREMIUM_FEATURES.map((f) => (
              <li key={f.label} className="flex items-center gap-2 text-sm">
                <Check className="h-4 w-4 text-amber-400 shrink-0" />
                <span className="text-gray-200">{f.label}</span>
              </li>
            ))}
          </ul>

          <div className="mt-6 space-y-3 relative">
            <button
              onClick={handlePremiumStart}
              disabled={loading}
              className="w-full rounded-lg bg-amber-500 py-3 text-sm font-bold text-black hover:bg-amber-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              {loading ? 'Ladowanie...' : '49 PLN / miesiac'}
              <Zap className="h-4 w-4" />
            </button>
            <p className="text-center text-xs text-gray-600">
              Anuluj kiedy chcesz. Bez zobowiazan.
            </p>
          </div>
        </div>
      </div>

      {/* Feature comparison table */}
      <div className="rounded-xl border border-gray-800 bg-[#121212] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">Porownanie funkcji</h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-xs text-gray-500">
              <th className="px-6 py-3 text-left font-medium">Funkcja</th>
              <th className="px-6 py-3 text-center font-medium">FREE</th>
              <th className="px-6 py-3 text-center font-medium text-amber-400">PREMIUM</th>
            </tr>
          </thead>
          <tbody>
            {[
              { feature: 'Optymalizacje / dzien', free: '3', premium: 'Bez limitu' },
              { feature: 'RAG Knowledge Base', free: false, premium: true },
              { feature: 'Keyword Intelligence', free: false, premium: true },
              { feature: 'Monitoring & Alerty', free: false, premium: true },
              { feature: 'Historia optymalizacji', free: false, premium: true },
              { feature: 'CSV Export', free: false, premium: true },
              { feature: 'Marketplace', free: 'Amazon', premium: 'Wszystkie' },
              { feature: 'Ranking Juice', free: 'Wynik', premium: 'Full breakdown' },
            ].map((row) => (
              <tr key={row.feature} className="border-b border-gray-800/50">
                <td className="px-6 py-3 text-gray-300">{row.feature}</td>
                <td className="px-6 py-3 text-center">
                  {typeof row.free === 'boolean' ? (
                    row.free ? (
                      <Check className="h-4 w-4 text-green-400 mx-auto" />
                    ) : (
                      <X className="h-4 w-4 text-gray-700 mx-auto" />
                    )
                  ) : (
                    <span className="text-gray-400">{row.free}</span>
                  )}
                </td>
                <td className="px-6 py-3 text-center">
                  {typeof row.premium === 'boolean' ? (
                    row.premium ? (
                      <Check className="h-4 w-4 text-amber-400 mx-auto" />
                    ) : (
                      <X className="h-4 w-4 text-gray-700 mx-auto" />
                    )
                  ) : (
                    <span className="text-amber-400 font-medium">{row.premium}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* License key recovery link */}
      <div className="text-center pb-4">
        <button
          onClick={() => router.push('/payment/recover')}
          className="text-gray-500 text-xs hover:text-gray-400 transition-colors"
        >
          Masz juz klucz? Odzyskaj go tutaj
        </button>
      </div>

      {isPremium && (
        <div className="text-center pb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-amber-400 text-sm hover:underline flex items-center gap-1 mx-auto"
          >
            Jestes Premium — przejdz do Dashboard
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  )
}
