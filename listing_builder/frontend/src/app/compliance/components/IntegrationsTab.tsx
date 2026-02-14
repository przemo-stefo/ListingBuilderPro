// frontend/src/app/compliance/components/IntegrationsTab.tsx
// Purpose: Marketplace integration cards — OAuth connect/disconnect + connection status
// NOT for: Managing tracked products (that's in monitoring page)

'use client'

import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Link2,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Unplug,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTrackedProducts } from '@/lib/hooks/useMonitoring'
import { useOAuthConnections, useOAuthAuthorize, useOAuthDisconnect } from '@/lib/hooks/useOAuth'
import { useToast } from '@/lib/hooks/useToast'

// WHY: Only amazon & allegro have OAuth flow ready — others are static cards
const OAUTH_MARKETPLACES = new Set(['amazon', 'allegro'])

const MARKETPLACES = [
  { id: 'amazon', name: 'Amazon Seller Central', desc: 'Europejskie rynki Amazon (DE, FR, IT, ES, PL)', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-orange-500/20' },
  { id: 'allegro', name: 'Allegro', desc: 'Najwiekszy marketplace w Polsce', flag: '\u{1F1F5}\u{1F1F1}', color: 'border-orange-500/20' },
  { id: 'ebay', name: 'eBay', desc: 'Globalna platforma aukcyjna i sprzedazowa', flag: '\u{1F1EC}\u{1F1E7}', color: 'border-blue-500/20' },
  { id: 'kaufland', name: 'Kaufland.de', desc: 'Jeden z najwiekszych marketplace w Niemczech', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-red-500/20' },
  { id: 'shopify', name: 'Shopify', desc: 'Wlasny sklep internetowy', flag: '\u{1F6D2}', color: 'border-green-500/20' },
  { id: 'otto', name: 'Otto.de', desc: 'Drugi co do wielkosci marketplace w Niemczech', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-gray-500/20' },
  { id: 'etsy', name: 'Etsy', desc: 'Platforma dla produktow handmade i vintage', flag: '\u{1F1FA}\u{1F1F8}', color: 'border-orange-500/20' },
  { id: 'bol', name: 'Bol.com', desc: 'Najwiekszy marketplace w Holandii i Belgii', flag: '\u{1F1F3}\u{1F1F1}', color: 'border-blue-500/20' },
]

export default function IntegrationsTab() {
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const trackedQuery = useTrackedProducts()
  const oauthQuery = useOAuthConnections()
  const authorizeMutation = useOAuthAuthorize()
  const disconnectMutation = useOAuthDisconnect()

  const tracked = trackedQuery.data?.items ?? []
  const oauthConns = oauthQuery.data?.connections ?? []

  // WHY: Show toast on OAuth redirect back (?oauth=success or ?oauth=error)
  useEffect(() => {
    const oauthResult = searchParams.get('oauth')
    if (oauthResult === 'success') {
      const mp = searchParams.get('marketplace') || ''
      toast({ title: 'Polaczono!', description: `${mp} OAuth zakonczone pomyslnie` })
    } else if (oauthResult === 'error') {
      const msg = searchParams.get('msg') || 'Nieznany blad'
      toast({ title: 'Blad OAuth', description: msg, variant: 'destructive' })
    }
  }, [searchParams, toast])

  // WHY: Merge tracked products (legacy) + OAuth connections for status
  const connectedByOAuth = new Set(oauthConns.filter(c => c.status === 'active').map(c => c.marketplace))
  const connectedByTracking = new Set(tracked.map(p => p.marketplace))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Link2 className="h-5 w-5 text-blue-400" />
          Integracje Marketplace
        </h2>
        <p className="text-sm text-gray-400">
          Polacz swoje konta, aby automatycznie monitorowac compliance
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {MARKETPLACES.map((mp) => {
          const hasOAuth = OAUTH_MARKETPLACES.has(mp.id)
          const oauthConn = oauthConns.find(c => c.marketplace === mp.id)
          const isOAuthActive = oauthConn?.status === 'active'
          const isTracked = connectedByTracking.has(mp.id)
          const isConnected = isOAuthActive || isTracked
          const productCount = tracked.filter(p => p.marketplace === mp.id).length

          return (
            <div
              key={mp.id}
              className={cn(
                'rounded-xl border bg-[#1A1A1A] p-5 transition-colors',
                isConnected ? mp.color : 'border-gray-800'
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{mp.flag}</span>
                  <div>
                    <p className="text-sm font-medium text-white">{mp.name}</p>
                    <p className="text-xs text-gray-500">{mp.desc}</p>
                  </div>
                </div>
                {isConnected && (
                  <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0" />
                )}
              </div>

              <div className="flex items-center justify-between">
                <div>
                  {isOAuthActive ? (
                    <span className="text-xs text-green-400">
                      OAuth aktywny{oauthConn?.seller_id ? ` (${oauthConn.seller_id})` : ''}
                    </span>
                  ) : isTracked ? (
                    <span className="text-xs text-green-400">
                      Polaczony &middot; {productCount} {productCount === 1 ? 'produkt' : 'produktow'}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-500">
                      {hasOAuth ? 'Nie polaczony' : 'Wkrotce'}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {hasOAuth && isOAuthActive && (
                    <button
                      onClick={() => disconnectMutation.mutate(mp.id)}
                      disabled={disconnectMutation.isPending}
                      className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                    >
                      <Unplug className="h-3 w-3" />
                      Rozlacz
                    </button>
                  )}
                  <button
                    onClick={() => hasOAuth && !isOAuthActive ? authorizeMutation.mutate(mp.id) : undefined}
                    disabled={!hasOAuth || isOAuthActive || authorizeMutation.isPending}
                    className={cn(
                      'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                      hasOAuth && !isOAuthActive
                        ? 'bg-white/5 text-white hover:bg-white/10 border border-gray-700'
                        : isOAuthActive
                          ? 'bg-gray-800 text-gray-400'
                          : 'bg-gray-800/50 text-gray-600 cursor-not-allowed'
                    )}
                  >
                    {authorizeMutation.isPending && authorizeMutation.variables === mp.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : isOAuthActive ? (
                      <>Ustawienia <ExternalLink className="h-3 w-3" /></>
                    ) : (
                      'Polacz'
                    )}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
