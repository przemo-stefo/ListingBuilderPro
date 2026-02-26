// frontend/src/app/compliance/components/IntegrationsTab.tsx
// Purpose: Marketplace integration cards — OAuth connect/disconnect + store scan
// NOT for: Managing tracked products (that's in monitoring page)

'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Link2,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Unplug,
  Search,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTrackedProducts } from '@/lib/hooks/useMonitoring'
import { useOAuthConnections, useOAuthAuthorize, useOAuthDisconnect } from '@/lib/hooks/useOAuth'
import { useToast } from '@/lib/hooks/useToast'
import { apiClient } from '@/lib/api/client'
import AmazonConnectForm from './AmazonConnectForm'
import BolConnectForm from './BolConnectForm'

// WHY: Marketplaces with OAuth flow ready — others show "Wkrótce"
// WHY bol: Uses Client Credentials (form-based), not browser redirect
const OAUTH_MARKETPLACES = new Set(['amazon', 'allegro', 'ebay', 'bol'])

const MARKETPLACES = [
  { id: 'amazon', name: 'Amazon Seller Central', desc: 'Europejskie rynki Amazon (DE, FR, IT, ES, PL)', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-orange-500/20' },
  { id: 'allegro', name: 'Allegro', desc: 'Największy marketplace w Polsce', flag: '\u{1F1F5}\u{1F1F1}', color: 'border-orange-500/20' },
  { id: 'ebay', name: 'eBay', desc: 'Globalna platforma aukcyjna i sprzedażowa', flag: '\u{1F1EC}\u{1F1E7}', color: 'border-blue-500/20' },
  { id: 'kaufland', name: 'Kaufland.de', desc: 'Jeden z największych marketplace w Niemczech', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-red-500/20' },
  { id: 'shopify', name: 'Shopify', desc: 'Własny sklep internetowy', flag: '\u{1F6D2}', color: 'border-green-500/20' },
  { id: 'otto', name: 'Otto.de', desc: 'Drugi co do wielkości marketplace w Niemczech', flag: '\u{1F1E9}\u{1F1EA}', color: 'border-gray-500/20' },
  { id: 'etsy', name: 'Etsy', desc: 'Platforma dla produktów handmade i vintage', flag: '\u{1F1FA}\u{1F1F8}', color: 'border-orange-500/20' },
  { id: 'bol', name: 'Bol.com', desc: 'Największy marketplace w Holandii i Belgii', flag: '\u{1F1F3}\u{1F1F1}', color: 'border-blue-500/20' },
]

export default function IntegrationsTab() {
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const trackedQuery = useTrackedProducts()
  const oauthQuery = useOAuthConnections()
  const authorizeMutation = useOAuthAuthorize()
  const disconnectMutation = useOAuthDisconnect()
  const [scanning, setScanning] = useState(false)
  // WHY: Amazon/BOL use form-based connect, not browser redirect
  const [amazonFormOpen, setAmazonFormOpen] = useState(false)
  const [bolFormOpen, setBolFormOpen] = useState(false)

  const tracked = trackedQuery.data?.items ?? []
  const oauthConns = oauthQuery.data?.connections ?? []

  // WHY: Show toast on OAuth redirect back (?oauth=success or ?oauth=error)
  useEffect(() => {
    const oauthResult = searchParams.get('oauth')
    if (oauthResult === 'success') {
      const mp = searchParams.get('marketplace') || ''
      toast({ title: 'Połączono!', description: `${mp} OAuth zakończone pomyślnie` })
    } else if (oauthResult === 'error') {
      const msg = searchParams.get('msg') || 'Nieznany błąd'
      toast({ title: 'Błąd OAuth', description: msg, variant: 'destructive' })
    }
  }, [searchParams, toast])

  // WHY: Tracked products (legacy) — used for marketplace status badges
  const connectedByTracking = new Set(tracked.map(p => p.marketplace))

  async function handleStoreScan() {
    setScanning(true)
    try {
      // WHY: apiClient sends JWT (raw fetch() was missing it → 401 after require_user_id fix)
      const { data } = await apiClient.post('/compliance/audit-store')
      toast({
        title: `Skan zakończony — ${data.overall_score}%`,
        description: `${data.total_products} produktów: ${data.compliant_count} OK, ${data.warning_count} ostrzeżeń, ${data.error_count} błędów`,
      })
    } catch {
      toast({
        title: 'Błąd połączenia',
        description: 'Nie udało się połączyć z serwerem',
        variant: 'destructive',
      })
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Link2 className="h-5 w-5 text-blue-400" />
          Integracje Marketplace
        </h2>
        <p className="text-sm text-gray-400">
          Połącz swoje konta, aby automatycznie monitorować compliance
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
                      Połączony &middot; {productCount} {productCount === 1 ? 'produkt' : 'produktów'}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-500">
                      {hasOAuth ? 'Nie połączony' : 'Wkrótce'}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {/* WHY: Store scan button only for Allegro with active OAuth */}
                  {mp.id === 'allegro' && isOAuthActive && (
                    <button
                      onClick={handleStoreScan}
                      disabled={scanning}
                      className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                    >
                      {scanning ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Search className="h-3 w-3" />
                      )}
                      {scanning ? 'Skanowanie...' : 'Skanuj produkty'}
                    </button>
                  )}
                  {hasOAuth && isOAuthActive && (
                    <button
                      onClick={() => disconnectMutation.mutate(mp.id)}
                      disabled={disconnectMutation.isPending}
                      className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                    >
                      <Unplug className="h-3 w-3" />
                      Rozłącz
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (!hasOAuth || isOAuthActive) return
                      // WHY: Amazon/BOL use form-based connect, others use browser redirect
                      if (mp.id === 'amazon') {
                        setAmazonFormOpen(true)
                      } else if (mp.id === 'bol') {
                        setBolFormOpen(true)
                      } else {
                        authorizeMutation.mutate(mp.id)
                      }
                    }}
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
                      'Połącz'
                    )}
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* WHY: Amazon/BOL — form-based connect, extracted to own components */}
      {amazonFormOpen && (
        <AmazonConnectForm
          onSuccess={() => { setAmazonFormOpen(false); oauthQuery.refetch() }}
          onCancel={() => setAmazonFormOpen(false)}
        />
      )}
      {bolFormOpen && (
        <BolConnectForm
          onSuccess={() => { setBolFormOpen(false); oauthQuery.refetch() }}
          onCancel={() => setBolFormOpen(false)}
        />
      )}
    </div>
  )
}
