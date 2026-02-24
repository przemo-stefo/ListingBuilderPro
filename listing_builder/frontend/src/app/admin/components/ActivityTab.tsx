// frontend/src/app/admin/components/ActivityTab.tsx
// Purpose: Activity log — recent optimizations, imports, compliance reports
// NOT for: Cost data or license management

'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api/client'

interface ActivityData {
  period_days: number
  optimizations: { id: number; title: string; marketplace: string; mode: string; client_ip: string; created_at: string }[]
  imports: { id: number; source: string; status: string; total_products: number; created_at: string }[]
  compliance_reports: { id: string; marketplace: string; total_products: number; overall_score: number; created_at: string }[]
}

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-500/10 text-green-400',
  running: 'bg-blue-500/10 text-blue-400',
  pending: 'bg-yellow-500/10 text-yellow-400',
  failed: 'bg-red-500/10 text-red-400',
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export function ActivityTab() {
  const [days, setDays] = useState(7)

  const { data, isLoading } = useQuery<ActivityData>({
    queryKey: ['admin-activity', days],
    queryFn: async () => {
      const res = await apiRequest<ActivityData>('get', `/admin/activity?days=${days}`)
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  const periods = [
    { label: '7 dni', value: 7 },
    { label: '14 dni', value: 14 },
    { label: '30 dni', value: 30 },
  ]

  if (isLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Ładowanie...</div>
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-1.5">
        {periods.map((p) => (
          <button
            key={p.value}
            onClick={() => setDays(p.value)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              days === p.value ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Optimizations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Optymalizacje ({data.optimizations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {data.optimizations.length === 0 ? (
            <p className="text-sm text-gray-500">Brak w tym okresie</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 text-left font-medium text-gray-400">Tytuł</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Marketplace</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Tryb</th>
                    <th className="pb-2 text-left font-medium text-gray-400">IP</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {data.optimizations.slice(0, 10).map((row) => (
                    <tr key={row.id} className="border-b border-gray-800/50">
                      <td className="py-2 text-white max-w-[200px] truncate">{row.title}</td>
                      <td className="py-2 text-gray-400">{row.marketplace}</td>
                      <td className="py-2 text-gray-400">{row.mode}</td>
                      <td className="py-2 text-gray-500 font-mono text-xs">{row.client_ip}</td>
                      <td className="py-2 text-gray-400">{row.created_at ? formatDate(row.created_at) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Imports */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Importy ({data.imports.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {data.imports.length === 0 ? (
            <p className="text-sm text-gray-500">Brak w tym okresie</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 text-left font-medium text-gray-400">Źródło</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Status</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Produkty</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {data.imports.map((row) => (
                    <tr key={row.id} className="border-b border-gray-800/50">
                      <td className="py-2 text-white">{row.source}</td>
                      <td className="py-2">
                        <Badge className={`text-xs ${STATUS_COLORS[row.status] || 'bg-gray-500/10 text-gray-400'}`}>
                          {row.status}
                        </Badge>
                      </td>
                      <td className="py-2 text-gray-400">{row.total_products}</td>
                      <td className="py-2 text-gray-400">{row.created_at ? formatDate(row.created_at) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Compliance Reports */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Raporty Compliance ({data.compliance_reports.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {data.compliance_reports.length === 0 ? (
            <p className="text-sm text-gray-500">Brak w tym okresie</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 text-left font-medium text-gray-400">Marketplace</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Produkty</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Score</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {data.compliance_reports.map((row) => (
                    <tr key={row.id} className="border-b border-gray-800/50">
                      <td className="py-2 text-white">{row.marketplace}</td>
                      <td className="py-2 text-gray-400">{row.total_products}</td>
                      <td className="py-2">
                        <span className={row.overall_score >= 80 ? 'text-green-400' : row.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'}>
                          {row.overall_score}%
                        </span>
                      </td>
                      <td className="py-2 text-gray-400">{row.created_at ? formatDate(row.created_at) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
