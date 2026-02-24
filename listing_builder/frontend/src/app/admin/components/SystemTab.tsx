// frontend/src/app/admin/components/SystemTab.tsx
// Purpose: System health dashboard — DB status, Groq keys, config
// NOT for: Business metrics or user data

'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api/client'
import { RefreshCw } from 'lucide-react'

interface SystemData {
  database: { status: string; pool_size?: number; checked_out?: number; error?: string }
  groq: {
    total_keys: number
    keys: { index: number; status: string; error: string | null }[]
  }
  config: {
    groq_model: string
    admin_emails: string[]
    cors_origins_count: number
    is_production: boolean
    rag_mode: string
  }
}

export function SystemTab() {
  const { data, isLoading, refetch, isFetching } = useQuery<SystemData>({
    queryKey: ['admin-system'],
    queryFn: async () => {
      const res = await apiRequest<SystemData>('get', '/admin/system')
      if (res.error) throw new Error(res.error)
      return res.data!
    },
    // WHY: Don't auto-refetch — Groq key check is slow (~5s)
    staleTime: 60_000,
  })

  if (isLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Sprawdzanie systemu...</div>
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Odśwież
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Database */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Baza danych</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Status</span>
              <Badge className={data.database.status === 'connected' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}>
                {data.database.status}
              </Badge>
            </div>
            {data.database.pool_size != null && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Pool size</span>
                <span className="text-sm text-white">{data.database.pool_size}</span>
              </div>
            )}
            {data.database.checked_out != null && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Checked out</span>
                <span className="text-sm text-white">{data.database.checked_out}</span>
              </div>
            )}
            {data.database.error && (
              <p className="text-xs text-red-400 break-all">{data.database.error}</p>
            )}
          </CardContent>
        </Card>

        {/* Groq Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Groq Keys ({data.groq.total_keys})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.groq.keys.map((key) => (
                <div key={key.index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Key #{key.index}</span>
                  <div className="flex items-center gap-2">
                    <Badge className={key.status === 'ok' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}>
                      {key.status}
                    </Badge>
                    {key.error && (
                      <span className="text-xs text-red-400 max-w-[120px] truncate" title={key.error}>
                        {key.error}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Config */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Konfiguracja</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Model</span>
              <span className="text-sm text-white font-mono">{data.config.groq_model}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">RAG mode</span>
              <span className="text-sm text-white">{data.config.rag_mode}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Środowisko</span>
              <Badge className={data.config.is_production ? 'bg-orange-500/10 text-orange-400' : 'bg-gray-500/10 text-gray-400'}>
                {data.config.is_production ? 'production' : 'development'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">CORS origins</span>
              <span className="text-sm text-white">{data.config.cors_origins_count}</span>
            </div>
            <div>
              <span className="text-sm text-gray-400">Admin emails</span>
              <div className="mt-1 space-y-1">
                {data.config.admin_emails.map((email) => (
                  <p key={email} className="text-xs text-gray-300 font-mono">{email}</p>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
