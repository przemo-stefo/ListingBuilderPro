// frontend/src/app/admin/page.tsx
// Purpose: Admin dashboard — 5 tabs: overview, users, activity, system, costs
// NOT for: User-facing features (this is Mateusz/Bartek admin view)

'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { StatCard } from '@/components/ui/StatCard'
import { apiRequest } from '@/lib/api/client'
import { useAdmin } from '@/lib/hooks/useAdmin'
import {
  ShieldX, KeyRound, Package, Sparkles, Search,
  Globe, AlertTriangle, DollarSign,
} from 'lucide-react'
import { CostsTab } from './components/CostsTab'
import { UsersTab } from './components/UsersTab'
import { ActivityTab } from './components/ActivityTab'
import { SystemTab } from './components/SystemTab'

// --- Types ---

interface AdminOverview {
  licenses: { total: number; active: number; expired: number; revoked: number }
  products: { total: number; imported: number; optimized: number; published: number; failed: number }
  usage_30d: { optimizer_runs: number; research_runs: number; unique_ips: number }
  oauth_connections: { total: number; active: number }
  alerts: { total: number; unacknowledged: number; critical: number }
  mrr_pln: number
}

type Tab = 'overview' | 'users' | 'activity' | 'system' | 'costs'

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Przegląd' },
  { key: 'users', label: 'Użytkownicy' },
  { key: 'activity', label: 'Aktywność' },
  { key: 'system', label: 'System' },
  { key: 'costs', label: 'Koszty API' },
]

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
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard icon={DollarSign} label="MRR" value={`${data.mrr_pln} PLN`} sub={`${data.licenses.active} aktywnych subskrypcji`} />
      <StatCard icon={KeyRound} label="Aktywne licencje" value={data.licenses.active.toString()} sub={`${data.licenses.total} łącznie`} />
      <StatCard icon={Package} label="Produkty" value={data.products.total.toString()} sub={`${data.products.optimized} zoptymalizowanych`} />
      <StatCard icon={Sparkles} label="Optymalizacje 30d" value={data.usage_30d.optimizer_runs.toString()} sub="ostatnie 30 dni" />
      <StatCard icon={Search} label="Research 30d" value={data.usage_30d.research_runs.toString()} sub="badania rynku" />
      <StatCard icon={Globe} label="Unikalne IP" value={data.usage_30d.unique_ips.toString()} sub="ostatnie 30 dni" />
      <StatCard icon={AlertTriangle} label="Alerty aktywne" value={data.alerts.unacknowledged.toString()} sub={`${data.alerts.critical} krytycznych`} />
    </div>
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
        <p className="text-sm text-gray-400">Przegląd systemu, użytkownicy, aktywność, system i koszty API</p>
      </div>

      {/* WHY: Tab bar — simple buttons, no external tab library needed */}
      <div className="flex gap-1 border-b border-gray-800 pb-px overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`whitespace-nowrap rounded-t-lg px-4 py-2 text-sm font-medium transition-colors ${
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
      {tab === 'users' && <UsersTab />}
      {tab === 'activity' && <ActivityTab />}
      {tab === 'system' && <SystemTab />}
      {tab === 'costs' && <CostsTab />}
    </div>
  )
}
