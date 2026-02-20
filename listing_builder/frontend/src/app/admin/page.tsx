// frontend/src/app/admin/page.tsx
// Purpose: Admin cost dashboard — API usage, spend per provider, daily trend
// NOT for: User-facing features (this is Mateusz's admin view)

'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api/client'
import { useAdmin } from '@/lib/hooks/useAdmin'
import {
  DollarSign,
  Zap,
  TrendingUp,
  BarChart3,
  Cpu,
  ShieldX,
} from 'lucide-react'

interface CostTotals {
  runs: number
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  total_cost_usd: number
  avg_cost_per_run_usd: number
}

interface ProviderRow {
  model: string
  runs: number
  tokens: number
  cost_usd: number
}

interface DailyRow {
  date: string
  runs: number
  tokens: number
  cost_usd: number
}

interface CostDashboard {
  period_days: number
  totals: CostTotals
  by_provider: ProviderRow[]
  daily: DailyRow[]
}

// WHY: Model name → friendly label mapping
const MODEL_LABELS: Record<string, string> = {
  'llama-3.3-70b-versatile': 'Groq (darmowy)',
  'gemini-2.0-flash': 'Gemini Flash',
  'gemini-2.5-pro-preview-06-05': 'Gemini Pro',
  'gpt-4o-mini': 'OpenAI GPT-4o Mini',
  'unknown': 'Nieznany',
}

function modelLabel(model: string): string {
  return MODEL_LABELS[model] || model
}

// WHY: Color coding — Groq=green (free), Gemini=blue, OpenAI=orange
function modelColor(model: string): string {
  if (model.includes('llama')) return 'text-green-400 bg-green-500/10'
  if (model.includes('gemini-2.0')) return 'text-blue-400 bg-blue-500/10'
  if (model.includes('gemini-2.5')) return 'text-cyan-400 bg-cyan-500/10'
  if (model.includes('gpt')) return 'text-orange-400 bg-orange-500/10'
  return 'text-gray-400 bg-gray-500/10'
}

function formatCost(usd: number): string {
  if (usd === 0) return '$0.00'
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

export default function AdminPage() {
  const { isAdmin, isLoading: adminLoading } = useAdmin()
  const [days, setDays] = useState(30)

  const { data, isLoading } = useQuery<CostDashboard>({
    queryKey: ['admin-costs', days],
    queryFn: async () => {
      const res = await apiRequest<CostDashboard>('get', `/admin/costs?days=${days}`)
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  const periods = [
    { label: '7 dni', value: 7 },
    { label: '30 dni', value: 30 },
    { label: '90 dni', value: 90 },
    { label: 'Rok', value: 365 },
  ]

  // WHY: Block non-admins from seeing the page even if they navigate directly
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Panel Administracyjny</h1>
          <p className="text-sm text-gray-400">Koszty API, zużycie tokenów i statystyki</p>
        </div>
        <div className="flex gap-1.5">
          {periods.map((p) => (
            <button
              key={p.value}
              onClick={() => setDays(p.value)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                days === p.value
                  ? 'bg-white text-black'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-gray-500">
          Ładowanie danych...
        </div>
      ) : data ? (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              icon={DollarSign}
              label="Koszt całkowity"
              value={formatCost(data.totals.total_cost_usd)}
              sub={`${days} dni`}
            />
            <StatCard
              icon={Zap}
              label="Optymalizacje"
              value={data.totals.runs.toString()}
              sub={`avg ${formatCost(data.totals.avg_cost_per_run_usd)}/szt`}
            />
            <StatCard
              icon={Cpu}
              label="Tokeny"
              value={formatTokens(data.totals.total_tokens)}
              sub={`${formatTokens(data.totals.prompt_tokens)} in / ${formatTokens(data.totals.completion_tokens)} out`}
            />
            <StatCard
              icon={TrendingUp}
              label="Avg/dzień"
              value={formatCost(data.totals.total_cost_usd / Math.max(days, 1))}
              sub={`${Math.round(data.totals.runs / Math.max(days, 1))} runs/dzień`}
            />
          </div>

          {/* Per-provider breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Koszty wg providera</CardTitle>
              <CardDescription>Rozbicie kosztów na modele AI</CardDescription>
            </CardHeader>
            <CardContent>
              {data.by_provider.length === 0 ? (
                <p className="text-sm text-gray-500">Brak danych w tym okresie</p>
              ) : (
                <div className="space-y-3">
                  {data.by_provider.map((row) => {
                    const pct = data.totals.runs > 0 ? (row.runs / data.totals.runs) * 100 : 0
                    return (
                      <div key={row.model} className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge className={`text-xs ${modelColor(row.model)}`}>
                              {modelLabel(row.model)}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {row.runs} runs · {formatTokens(row.tokens)} tokenów
                            </span>
                          </div>
                          <span className="text-sm font-medium text-white">
                            {formatCost(row.cost_usd)}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-800">
                          <div
                            className="h-2 rounded-full bg-white/20 transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Daily trend table */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-gray-400" />
                <CardTitle className="text-lg">Trend dzienny</CardTitle>
              </div>
              <CardDescription>Zużycie API dzień po dniu</CardDescription>
            </CardHeader>
            <CardContent>
              {data.daily.length === 0 ? (
                <p className="text-sm text-gray-500">Brak danych w tym okresie</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-800">
                        <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                        <th className="pb-2 text-right font-medium text-gray-400">Runs</th>
                        <th className="pb-2 text-right font-medium text-gray-400">Tokeny</th>
                        <th className="pb-2 text-right font-medium text-gray-400">Koszt</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.daily.map((row) => (
                        <tr key={row.date} className="border-b border-gray-800/50">
                          <td className="py-2 text-gray-300">{row.date}</td>
                          <td className="py-2 text-right text-white">{row.runs}</td>
                          <td className="py-2 text-right text-gray-400">{formatTokens(row.tokens)}</td>
                          <td className="py-2 text-right font-mono text-white">{formatCost(row.cost_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  )
}

// WHY: Reusable stat card — keeps the grid DRY
function StatCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  sub: string
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-white/5 p-2">
            <Icon className="h-5 w-5 text-gray-400" />
          </div>
          <div>
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
            <p className="text-[11px] text-gray-500">{sub}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
