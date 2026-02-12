// frontend/src/app/compliance/components/IntegrationsTab.tsx
// Purpose: Marketplace integration cards — show connection status based on tracked products
// NOT for: Managing tracked products (that's in monitoring page)

'use client'

import {
  Link2,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTrackedProducts } from '@/lib/hooks/useMonitoring'

// WHY: Static marketplace list — not all have backend integrations yet
const MARKETPLACES = [
  { id: 'amazon', name: 'Amazon Seller Central', desc: 'Europejskie rynki Amazon (DE, FR, IT, ES, PL)', flag: '🇩🇪', color: 'border-orange-500/20' },
  { id: 'ebay', name: 'eBay', desc: 'Globalna platforma aukcyjna i sprzedażowa', flag: '🇬🇧', color: 'border-blue-500/20' },
  { id: 'kaufland', name: 'Kaufland.de', desc: 'Jeden z największych marketplace w Niemczech', flag: '🇩🇪', color: 'border-red-500/20' },
  { id: 'allegro', name: 'Allegro', desc: 'Największy marketplace w Polsce', flag: '🇵🇱', color: 'border-orange-500/20' },
  { id: 'shopify', name: 'Shopify', desc: 'Własny sklep internetowy', flag: '🛒', color: 'border-green-500/20' },
  { id: 'woocommerce', name: 'WooCommerce', desc: 'Sklep oparty na WordPress', flag: '🛒', color: 'border-purple-500/20' },
  { id: 'otto', name: 'Otto.de', desc: 'Drugi co do wielkości marketplace w Niemczech', flag: '🇩🇪', color: 'border-gray-500/20' },
  { id: 'etsy', name: 'Etsy', desc: 'Platforma dla produktów handmade i vintage', flag: '🇺🇸', color: 'border-orange-500/20' },
  { id: 'zalando', name: 'Zalando', desc: 'Europejska platforma modowa', flag: '🇩🇪', color: 'border-orange-500/20' },
  { id: 'cdiscount', name: 'Cdiscount', desc: 'Wiodący marketplace we Francji', flag: '🇫🇷', color: 'border-blue-500/20' },
  { id: 'bol', name: 'Bol.com', desc: 'Największy marketplace w Holandii i Belgii', flag: '🇳🇱', color: 'border-blue-500/20' },
]

export default function IntegrationsTab() {
  const trackedQuery = useTrackedProducts()
  const tracked = trackedQuery.data?.items ?? []

  // WHY: A marketplace is "connected" if it has any tracked products
  const connectedMarketplaces = new Set(tracked.map((p) => p.marketplace))

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
          const isConnected = connectedMarketplaces.has(mp.id)
          const productCount = tracked.filter((p) => p.marketplace === mp.id).length

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
                {isConnected ? (
                  <span className="text-xs text-green-400">
                    Połączony &middot; {productCount} {productCount === 1 ? 'produkt' : 'produktów'}
                  </span>
                ) : (
                  <span className="text-xs text-gray-500">Nie połączony</span>
                )}

                <button
                  className={cn(
                    'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                    isConnected
                      ? 'bg-gray-800 text-gray-400 hover:text-white'
                      : 'bg-white/5 text-white hover:bg-white/10 border border-gray-700'
                  )}
                >
                  {isConnected ? (
                    <>Ustawienia <ExternalLink className="h-3 w-3" /></>
                  ) : (
                    'Połącz'
                  )}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
