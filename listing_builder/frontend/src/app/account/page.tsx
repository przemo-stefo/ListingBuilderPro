// frontend/src/app/account/page.tsx
// Purpose: Account page — subscription status, billing management, user info, company data
// NOT for: Settings or marketplace connections

'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { useTier } from '@/lib/hooks/useTier'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { User, CreditCard, LogOut, Building2, Check } from 'lucide-react'
import { apiClient } from '@/lib/api/client'

interface SubscriptionInfo {
  plan: string
  status: string
  customer_id: string | null
  renewal_date: number | null
  email?: string
}

interface CompanyData {
  company_name: string
  nip: string
  address: string
  city: string
  postal_code: string
  country: string
}

const EMPTY_COMPANY: CompanyData = {
  company_name: '', nip: '', address: '', city: '', postal_code: '', country: 'Polska',
}

const INPUT_CLS = 'w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:border-gray-500 focus:outline-none'

export default function AccountPage() {
  const { user, signOut } = useAuth()
  const { tier } = useTier()
  const [sub, setSub] = useState<SubscriptionInfo | null>(null)
  const [portalLoading, setPortalLoading] = useState(false)
  const [company, setCompany] = useState<CompanyData>(EMPTY_COMPANY)
  const [companySaving, setCompanySaving] = useState(false)
  const [companySaved, setCompanySaved] = useState(false)
  const [companyError, setCompanyError] = useState('')

  useEffect(() => {
    apiClient.get('/stripe/subscription')
      .then(res => { if (res.data) setSub(res.data) })
      .catch(() => {})

    apiClient.get('/settings')
      .then(res => {
        if (res.data?.company) setCompany({ ...EMPTY_COMPANY, ...res.data.company })
      })
      .catch(() => {})
  }, [])

  const handlePortal = async () => {
    setPortalLoading(true)
    try {
      const { data } = await apiClient.post('/stripe/portal-session')
      if (data.portal_url) window.location.href = data.portal_url
    } finally {
      setPortalLoading(false)
    }
  }

  const handleCheckout = async () => {
    if (!user?.email) return
    try {
      const { data } = await apiClient.post('/stripe/create-checkout', {
        plan_type: 'monthly', email: user.email,
      })
      if (data.checkout_url) window.location.href = data.checkout_url
    } catch {}
  }

  const handleCompanySave = async () => {
    setCompanySaving(true)
    setCompanyError('')
    try {
      await apiClient.put('/settings', { company })
      setCompanySaved(true)
      setTimeout(() => setCompanySaved(false), 2000)
    } catch {
      setCompanyError('Nie udało się zapisać. Spróbuj ponownie.')
    } finally {
      setCompanySaving(false)
    }
  }

  const renewalDate = sub?.renewal_date
    ? new Date(sub.renewal_date * 1000).toLocaleDateString('pl-PL')
    : null

  const set = (field: keyof CompanyData) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setCompany(c => ({ ...c, [field]: e.target.value }))

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold text-white">Konto</h1>
        <p className="text-gray-400 mt-2">Zarządzaj kontem i subskrypcją</p>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <User className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-base">Profil</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Row label="Email" value={user?.email || '—'} />
          <Row label="ID użytkownika" value={`${user?.id?.slice(0, 8) || '—'}...`} mono />
          <Row label="Data rejestracji" value={user?.created_at ? new Date(user.created_at).toLocaleDateString('pl-PL') : '—'} />
        </CardContent>
      </Card>

      {/* Company data */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <Building2 className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-base">Dane firmowe</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Nazwa firmy" value={company.company_name} onChange={set('company_name')} placeholder="np. VIAREGIA.ONLINE Sp. z o.o." span={2} />
            <Field label="NIP" value={company.nip} onChange={set('nip')} placeholder="0000000000" />
            <Field label="Kraj" value={company.country} onChange={set('country')} />
            <Field label="Adres" value={company.address} onChange={set('address')} placeholder="ul. Przykładowa 10" span={2} />
            <Field label="Kod pocztowy" value={company.postal_code} onChange={set('postal_code')} placeholder="00-000" />
            <Field label="Miasto" value={company.city} onChange={set('city')} placeholder="Warszawa" />
          </div>
          {companyError && <p className="text-xs text-red-400">{companyError}</p>}
          <button
            onClick={handleCompanySave}
            disabled={companySaving}
            className="w-full rounded-lg border border-gray-700 py-2.5 text-sm text-white hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {companySaved ? (
              <><Check className="h-4 w-4 text-green-400" /> Zapisano</>
            ) : companySaving ? 'Zapisywanie...' : 'Zapisz dane firmowe'}
          </button>
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
              tier === 'premium' ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-400'
            }`}>
              {tier === 'premium' ? 'Aktywny' : 'Free'}
            </span>
          </div>

          {tier === 'premium' && sub?.customer_id ? (
            <button onClick={handlePortal} disabled={portalLoading}
              className="w-full rounded-lg border border-gray-700 py-2.5 text-sm text-white hover:bg-gray-800 transition-colors disabled:opacity-50">
              {portalLoading ? 'Ładowanie...' : 'Zarządzaj subskrypcją'}
            </button>
          ) : (
            <button onClick={handleCheckout}
              className="w-full rounded-lg bg-white py-2.5 text-sm font-medium text-black hover:bg-gray-200 transition-colors">
              Kup Premium — 49 PLN/mies.
            </button>
          )}
        </CardContent>
      </Card>

      <button onClick={signOut}
        className="flex items-center gap-2 rounded-lg border border-gray-800 px-4 py-2.5 text-sm text-gray-400 hover:border-red-800 hover:text-red-400 transition-colors">
        <LogOut className="h-4 w-4" />
        Wyloguj się
      </button>
    </div>
  )
}

// WHY: DRY helpers — avoid repeating className strings and layout patterns

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-400">{label}</span>
      <span className={`text-white ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>
    </div>
  )
}

function Field({ label, value, onChange, placeholder, span }: {
  label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string; span?: number
}) {
  return (
    <div className={span === 2 ? 'col-span-2' : ''}>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <input type="text" value={value} onChange={onChange} placeholder={placeholder} className={INPUT_CLS} />
    </div>
  )
}
