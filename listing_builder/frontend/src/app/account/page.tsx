// frontend/src/app/account/page.tsx
// Purpose: Account page — subscription status, billing management, user info
// NOT for: Settings or marketplace connections

'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { useTier } from '@/lib/hooks/useTier'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { User, CreditCard, LogOut } from 'lucide-react'

interface SubscriptionInfo {
  plan: string
  status: string
  customer_id: string | null
  renewal_date: number | null
  email?: string
}

export default function AccountPage() {
  const { user, signOut } = useAuth()
  const { tier } = useTier()
  const [sub, setSub] = useState<SubscriptionInfo | null>(null)
  const [portalLoading, setPortalLoading] = useState(false)

  useEffect(() => {
    fetch('/api/proxy/stripe/subscription')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setSub(data) })
      .catch(() => {})
  }, [])

  const handlePortal = async () => {
    setPortalLoading(true)
    try {
      const resp = await fetch('/api/proxy/stripe/portal-session', { method: 'POST' })
      const data = await resp.json()
      if (data.portal_url) {
        window.location.href = data.portal_url
      }
    } finally {
      setPortalLoading(false)
    }
  }

  const handleCheckout = async () => {
    if (!user?.email) return
    try {
      const resp = await fetch('/api/proxy/stripe/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_type: 'monthly', email: user.email }),
      })
      const data = await resp.json()
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    } catch {}
  }

  const renewalDate = sub?.renewal_date
    ? new Date(sub.renewal_date * 1000).toLocaleDateString('pl-PL')
    : null

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold text-white">Konto</h1>
        <p className="text-gray-400 mt-2">Zarządzaj kontem i subskrypcją</p>
      </div>

      {/* User info */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <User className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-base">Profil</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Email</span>
            <span className="text-white">{user?.email || '—'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">ID użytkownika</span>
            <span className="text-white font-mono text-xs">{user?.id?.slice(0, 8) || '—'}...</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Data rejestracji</span>
            <span className="text-white">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString('pl-PL') : '—'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Subscription */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <CreditCard className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-base">Plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-white">
                {tier === 'premium' ? 'Premium' : 'Darmowy'}
              </p>
              {tier === 'premium' && renewalDate && (
                <p className="text-xs text-gray-400">Odnowienie: {renewalDate}</p>
              )}
              {tier === 'free' && (
                <p className="text-xs text-gray-400">3 optymalizacje dziennie, tylko Amazon</p>
              )}
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${
              tier === 'premium'
                ? 'bg-green-900/40 text-green-400'
                : 'bg-gray-800 text-gray-400'
            }`}>
              {tier === 'premium' ? 'Aktywny' : 'Free'}
            </span>
          </div>

          {tier === 'premium' && sub?.customer_id ? (
            <button
              onClick={handlePortal}
              disabled={portalLoading}
              className="w-full rounded-lg border border-gray-700 py-2.5 text-sm text-white hover:bg-gray-800 transition-colors disabled:opacity-50"
            >
              {portalLoading ? 'Ładowanie...' : 'Zarządzaj subskrypcją'}
            </button>
          ) : (
            <button
              onClick={handleCheckout}
              className="w-full rounded-lg bg-white py-2.5 text-sm font-medium text-black hover:bg-gray-200 transition-colors"
            >
              Kup Premium — 49 PLN/mies.
            </button>
          )}
        </CardContent>
      </Card>

      {/* Sign out */}
      <button
        onClick={signOut}
        className="flex items-center gap-2 rounded-lg border border-gray-800 px-4 py-2.5 text-sm text-gray-400 hover:border-red-800 hover:text-red-400 transition-colors"
      >
        <LogOut className="h-4 w-4" />
        Wyloguj się
      </button>
    </div>
  )
}
