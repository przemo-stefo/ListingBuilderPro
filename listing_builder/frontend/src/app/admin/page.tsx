// frontend/src/app/admin/page.tsx
// Purpose: Admin dashboard — overview, licenses, API costs (tabbed layout)
// NOT for: User-facing features (this is Mateusz/Bartek admin view)

'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StatCard } from '@/components/ui/StatCard'
import { apiRequest } from '@/lib/api/client'
import { useAdmin } from '@/lib/hooks/useAdmin'
import {
  ShieldX, KeyRound, Package, Sparkles, Search,
  Globe, AlertTriangle,
} from 'lucide-react'
import { CostsTab } from './components/CostsTab'

// --- Types ---

interface AdminOverview {
  licenses: { total: number; active: number; expired: number; revoked: number }
  products: { total: number; imported: number; optimized: number; published: number; failed: number }
  usage_30d: { optimizer_runs: number; research_runs: number; unique_ips: number }
  oauth_connections: { total: number; active: number }
  alerts: { total: number; unacknowledged: number; critical: number }
}

interface LicenseItem {
  email: string
  status: string
  plan_type: string
  expires_at: string | null
  created_at: string | null
}

type Tab = 'overview' | 'licenses' | 'costs'

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Przegląd' },
  { key: 'licenses', label: 'Licencje' },
  { key: 'costs', label: 'Koszty API' },
]

// WHY: Status → color for license badges
const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-500/10 text-green-400',
  expired: 'bg-yellow-500/10 text-yellow-400',
  revoked: 'bg-red-500/10 text-red-400',
}

// --- Overview Tab ---

function OverviewTab() {
  const { data, isLoading } = useQuery<AdminOverview>({
    queryKey: ['admin-overview'],
    queryFn: async () => {
      const res = await apiRequest<AdminOverview>('get', '/admin/overview')
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  if (isLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Ładowanie...</div>
  }

  if (!data) return null

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard icon={KeyRound} label="Aktywne licencje" value={data.licenses.active.toString()} sub={`${data.licenses.total} łącznie`} />
      <StatCard icon={Package} label="Produkty" value={data.products.total.toString()} sub={`${data.products.optimized} zoptymalizowanych`} />
      <StatCard icon={Sparkles} label="Optymalizacje 30d" value={data.usage_30d.optimizer_runs.toString()} sub="ostatnie 30 dni" />
      <StatCard icon={Search} label="Research 30d" value={data.usage_30d.research_runs.toString()} sub="badania rynku" />
      <StatCard icon={Globe} label="Unikalne IP" value={data.usage_30d.unique_ips.toString()} sub="ostatnie 30 dni" />
      <StatCard icon={AlertTriangle} label="Alerty aktywne" value={data.alerts.unacknowledged.toString()} sub={`${data.alerts.critical} krytycznych`} />
    </div>
  )
}

// --- Licenses Tab ---

function LicensesTab() {
  const { data, isLoading } = useQuery<{ items: LicenseItem[]; total: number }>({
    queryKey: ['admin-licenses'],
    queryFn: async () => {
      const res = await apiRequest<{ items: LicenseItem[]; total: number }>('get', '/admin/licenses?limit=50')
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  if (isLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Ładowanie...</div>
  }

  if (!data || data.items.length === 0) {
    return <p className="text-center py-12 text-gray-500">Brak licencji</p>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Licencje ({data.total})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="pb-2 text-left font-medium text-gray-400">Email</th>
                <th className="pb-2 text-left font-medium text-gray-400">Status</th>
                <th className="pb-2 text-left font-medium text-gray-400">Plan</th>
                <th className="pb-2 text-left font-medium text-gray-400">Wygasa</th>
                <th className="pb-2 text-left font-medium text-gray-400">Utworzono</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((lic, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  <td className="py-2 text-white">{lic.email}</td>
                  <td className="py-2">
                    <Badge className={`text-xs ${STATUS_COLORS[lic.status] || 'bg-gray-500/10 text-gray-400'}`}>
                      {lic.status}
                    </Badge>
                  </td>
                  <td className="py-2 text-gray-400">{lic.plan_type}</td>
                  <td className="py-2 text-gray-400">{lic.expires_at ? new Date(lic.expires_at).toLocaleDateString('pl-PL') : '—'}</td>
                  <td className="py-2 text-gray-400">{lic.created_at ? new Date(lic.created_at).toLocaleDateString('pl-PL') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Main Page ---

export default function AdminPage() {
  const { isAdmin, isLoading: adminLoading } = useAdmin()
  const [tab, setTab] = useState<Tab>('overview')

  if (adminLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Sprawdzanie uprawnień...</div>
  }

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-500">
        <ShieldX className="h-12 w-12 mb-4 text-gray-600" />
        <p className="text-lg font-medium text-white">Brak dostępu</p>
        <p className="text-sm">Ta sekcja jest dostępna tylko dla administratorów.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Panel Administracyjny</h1>
        <p className="text-sm text-gray-400">Przegląd systemu, licencje i koszty API</p>
      </div>

      {/* WHY: Tab bar — simple buttons, no external tab library needed */}
      <div className="flex gap-1 border-b border-gray-800 pb-px">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-t-lg px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-gray-800 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <OverviewTab />}
      {tab === 'licenses' && <LicensesTab />}
      {tab === 'costs' && <CostsTab />}
    </div>
  )
}
