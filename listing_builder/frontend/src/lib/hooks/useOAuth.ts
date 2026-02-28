// frontend/src/lib/hooks/useOAuth.ts
// Purpose: React Query hooks for OAuth marketplace connections
// NOT for: Direct API calls (those are in lib/api/oauth.ts)

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchOAuthConnections, getAuthorizeUrl, disconnectMarketplace } from '../api/oauth'
import { useToast } from './useToast'
import { safeRedirect } from '../utils/redirect'

export function useOAuthConnections() {
  return useQuery({
    queryKey: ['oauth-connections'],
    queryFn: fetchOAuthConnections,
    staleTime: 30_000,
  })
}

export function useOAuthAuthorize() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (marketplace: string) => getAuthorizeUrl(marketplace),
    onSuccess: (data) => {
      // WHY: Redirect user to marketplace OAuth page
      safeRedirect(data.authorize_url)
    },
    onError: (error: Error) => {
      toast({ title: 'Blad OAuth', description: error.message, variant: 'destructive' })
    },
  })
}

export function useOAuthDisconnect() {
  const { toast } = useToast()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (marketplace: string) => disconnectMarketplace(marketplace),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['oauth-connections'] })
      toast({ title: 'Rozlaczono' })
    },
    onError: (error: Error) => {
      toast({ title: 'Blad rozlaczania', description: error.message, variant: 'destructive' })
    },
  })
}
