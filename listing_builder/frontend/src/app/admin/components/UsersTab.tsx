// frontend/src/app/admin/components/UsersTab.tsx
// Purpose: License management with revoke/extend actions + OAuth connections
// NOT for: Cost data or system health (those are separate tabs)

'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest } from '@/lib/api/client'

interface LicenseItem {
  id: string
  email: string
  status: string
  plan_type: string
  expires_at: string | null
  created_at: string | null
}

interface OAuthItem {
  user_id: string
  marketplace: string
  status: string
  seller_name: string | null
  created_at: string | null
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-500/10 text-green-400',
  expired: 'bg-yellow-500/10 text-yellow-400',
  revoked: 'bg-red-500/10 text-red-400',
}

export function UsersTab() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery<{ items: LicenseItem[]; total: number }>({
    queryKey: ['admin-licenses'],
    queryFn: async () => {
      const res = await apiRequest<{ items: LicenseItem[]; total: number }>('get', '/admin/licenses?limit=50')
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  const { data: oauthData } = useQuery<{ items: OAuthItem[] }>({
    queryKey: ['admin-oauth'],
    queryFn: async () => {
      const res = await apiRequest<{ items: OAuthItem[] }>('get', '/admin/oauth-connections')
      if (res.error) throw new Error(res.error)
      return res.data!
    },
  })

  const revokeMutation = useMutation({
    mutationFn: async (licenseId: string) => {
      const res = await apiRequest('patch', `/admin/licenses/${licenseId}`, { action: 'revoke' })
      if (res.error) throw new Error(res.error)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-licenses'] })
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] })
    },
  })

  const extendMutation = useMutation({
    mutationFn: async (licenseId: string) => {
      const res = await apiRequest('patch', `/admin/licenses/${licenseId}`, { action: 'extend', days: 30 })
      if (res.error) throw new Error(res.error)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-licenses'] })
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] })
    },
  })

  if (isLoading) {
    return <div className="flex items-center justify-center py-12 text-gray-500">Ładowanie...</div>
  }

  if (!data || data.items.length === 0) {
    return <p className="text-center py-12 text-gray-500">Brak licencji</p>
  }

  return (
    <div className="space-y-6">
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
                  <th className="pb-2 text-right font-medium text-gray-400">Akcje</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((lic) => (
                  <tr key={lic.id} className="border-b border-gray-800/50">
                    <td className="py-2 text-white">{lic.email}</td>
                    <td className="py-2">
                      <Badge className={`text-xs ${STATUS_COLORS[lic.status] || 'bg-gray-500/10 text-gray-400'}`}>
                        {lic.status}
                      </Badge>
                    </td>
                    <td className="py-2 text-gray-400">{lic.plan_type}</td>
                    <td className="py-2 text-gray-400">
                      {lic.expires_at ? new Date(lic.expires_at).toLocaleDateString('pl-PL') : '—'}
                    </td>
                    <td className="py-2 text-gray-400">
                      {lic.created_at ? new Date(lic.created_at).toLocaleDateString('pl-PL') : '—'}
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex justify-end gap-2">
                        {lic.status === 'active' && (
                          <button
                            onClick={() => revokeMutation.mutate(lic.id)}
                            disabled={revokeMutation.isPending}
                            className="rounded px-2 py-1 text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 disabled:opacity-50"
                          >
                            Revoke
                          </button>
                        )}
                        <button
                          onClick={() => extendMutation.mutate(lic.id)}
                          disabled={extendMutation.isPending}
                          className="rounded px-2 py-1 text-xs font-medium bg-green-500/10 text-green-400 hover:bg-green-500/20 disabled:opacity-50"
                        >
                          +30 dni
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* OAuth Connections */}
      {oauthData && oauthData.items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">OAuth Connections ({oauthData.items.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 text-left font-medium text-gray-400">User</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Marketplace</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Seller</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Status</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {oauthData.items.map((conn, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2 text-white font-mono text-xs">{conn.user_id}</td>
                      <td className="py-2 text-gray-300">{conn.marketplace}</td>
                      <td className="py-2 text-gray-400">{conn.seller_name || '—'}</td>
                      <td className="py-2">
                        <Badge className={`text-xs ${STATUS_COLORS[conn.status] || 'bg-gray-500/10 text-gray-400'}`}>
                          {conn.status}
                        </Badge>
                      </td>
                      <td className="py-2 text-gray-400">
                        {conn.created_at ? new Date(conn.created_at).toLocaleDateString('pl-PL') : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
