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
import { connectBol } from '@/lib/api/oauth'

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
  // WHY: BOL uses Client Credentials — user enters keys in a form, not browser redirect
  const [bolForm, setBolForm] = useState({ open: false, clientId: '', clientSecret: '', loading: false })

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

  // WHY: Merge tracked products (legacy) + OAuth connections for status
  const connectedByOAuth = new Set(oauthConns.filter(c => c.status === 'active').map(c => c.marketplace))
  const connectedByTracking = new Set(tracked.map(p => p.marketplace))

  async function handleStoreScan() {
    setScanning(true)
    try {
      const resp = await fetch('/api/proxy/compliance/audit-store', { method: 'POST' })
      const data = await resp.json()

      if (!resp.ok) {
        toast({
          title: 'Błąd skanowania',
          description: data.detail || 'Nie udało się przeskanować sklepu',
          variant: 'destructive',
        })
        return
      }

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

  async function handleBolConnect() {
    if (!bolForm.clientId.trim() || !bolForm.clientSecret.trim()) {
      toast({ title: 'Uzupełnij dane', description: 'Podaj Client ID i Client Secret', variant: 'destructive' })
      return
    }
    setBolForm(f => ({ ...f, loading: true }))
    try {
      await connectBol(bolForm.clientId.trim(), bolForm.clientSecret.trim())
      toast({ title: 'Połączono!', description: 'BOL.com podłączony pomyślnie' })
      setBolForm({ open: false, clientId: '', clientSecret: '', loading: false })
      oauthQuery.refetch()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Nieprawidłowe dane'
      toast({ title: 'Błąd BOL.com', description: msg, variant: 'destructive' })
      setBolForm(f => ({ ...f, loading: false }))
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
                      // WHY: BOL uses form-based connect, others use browser redirect
                      if (mp.id === 'bol') {
                        setBolForm(f => ({ ...f, open: true }))
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

      {/* WHY inline form: BOL Client Credentials don't need browser redirect — simple form */}
      {bolForm.open && (
        <div className="rounded-xl border border-blue-500/30 bg-[#121212] p-5 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-white">Połącz BOL.com</h3>
            <p className="text-xs text-gray-400 mt-1">
              Wpisz Client ID i Client Secret z BOL Partner Platform
            </p>
          </div>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Client ID"
              value={bolForm.clientId}
              onChange={e => setBolForm(f => ({ ...f, clientId: e.target.value }))}
              className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            />
            <input
              type="password"
              placeholder="Client Secret"
              value={bolForm.clientSecret}
              onChange={e => setBolForm(f => ({ ...f, clientSecret: e.target.value }))}
              className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleBolConnect}
              disabled={bolForm.loading}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-500 transition-colors disabled:opacity-50"
            >
              {bolForm.loading && <Loader2 className="h-3 w-3 animate-spin" />}
              {bolForm.loading ? 'Łączenie...' : 'Połącz'}
            </button>
            <button
              onClick={() => setBolForm({ open: false, clientId: '', clientSecret: '', loading: false })}
              className="rounded-lg px-4 py-2 text-xs text-gray-400 hover:text-white transition-colors"
            >
              Anuluj
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
