// frontend/src/app/compliance/components/AlertSettingsTab.tsx
// Purpose: Alert type toggles — create/enable/disable alert configurations
// NOT for: Viewing fired alerts (that's AlertsTab)

'use client'

import { useState } from 'react'
import {
  Bell,
  DollarSign,
  ShoppingCart,
  Package,
  XCircle,
  ShieldAlert,
  RotateCcw,
  Star,
  Truck,
  FileWarning,
  Tag,
  BarChart3,
  Users,
  CreditCard,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlertConfigs, useCreateAlertConfig, useToggleAlertConfig } from '@/lib/hooks/useMonitoring'
import type { AlertConfig } from '@/lib/types'

type SubTab = 'marketplace' | 'ecommerce'

// WHY: Alert types map to backend alert_type enum + static extras for future expansion
const MARKETPLACE_ALERT_TYPES = [
  { type: 'price_change', name: 'Zmiana ceny', desc: 'Powiadomienie gdy cena produktu zmieni się powyżej progu', icon: DollarSign },
  { type: 'buy_box_lost', name: 'Utrata Buy Box', desc: 'Alert gdy stracisz Buy Box na Amazon', icon: ShoppingCart },
  { type: 'low_stock', name: 'Niski stan magazynowy', desc: 'Ostrzeżenie gdy zapas spada poniżej minimum', icon: Package },
  { type: 'listing_deactivated', name: 'Dezaktywacja oferty', desc: 'Alert gdy oferta zostanie dezaktywowana', icon: XCircle },
  { type: 'compliance_fail', name: 'Naruszenie compliance', desc: 'Wykryto problemy ze zgodnością produktu', icon: ShieldAlert },
  { type: 'competitor_price', name: 'Cena konkurencji', desc: 'Konkurent zmienił cenę na Twój produkt', icon: Tag },
  { type: 'ranking_drop', name: 'Spadek rankingu', desc: 'Pozycja produktu spadła w wynikach wyszukiwania', icon: BarChart3 },
  { type: 'new_review', name: 'Nowa recenzja', desc: 'Nowa recenzja produktu na marketplace', icon: Star },
]

const ECOMMERCE_ALERT_TYPES = [
  { type: 'return_spike', name: 'Skok zwrotów', desc: 'Wykryto nietypowy wzrost zwrotów produktu', icon: RotateCcw },
  { type: 'negative_review', name: 'Negatywna opinia', desc: 'Nowa negatywna opinia (1-2 gwiazdki)', icon: Star },
  { type: 'shipping_delay', name: 'Opóźnienie wysyłki', desc: 'Zamówienie nie zostało wysłane w terminie', icon: Truck },
  { type: 'policy_violation', name: 'Naruszenie regulaminu', desc: 'Wykryto naruszenie zasad marketplace', icon: FileWarning },
  { type: 'account_health', name: 'Zdrowie konta', desc: 'Metryki konta sprzedawcy poniżej normy', icon: Users },
  { type: 'payment_issue', name: 'Problem z płatnością', desc: 'Wykryto problem z rozliczeniami', icon: CreditCard },
]

export default function AlertSettingsTab() {
  const [subTab, setSubTab] = useState<SubTab>('marketplace')
  const configsQuery = useAlertConfigs()
  const createMutation = useCreateAlertConfig()
  const toggleMutation = useToggleAlertConfig()

  const configs = (configsQuery.data?.items ?? []) as AlertConfig[]
  const activeCount = configs.filter((c) => c.enabled).length

  const alertTypes = subTab === 'marketplace' ? MARKETPLACE_ALERT_TYPES : ECOMMERCE_ALERT_TYPES

  // WHY: Check if an alert type already has a config in the backend
  const getConfig = (alertType: string) => configs.find((c) => c.alert_type === alertType)

  const handleToggle = async (alertType: string, name: string) => {
    const existing = getConfig(alertType)
    if (existing) {
      toggleMutation.mutate(existing.id)
    } else {
      // WHY: First toggle creates the config with enabled=true
      createMutation.mutate({ alert_type: alertType, name, enabled: true })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with active count */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Bell className="h-5 w-5 text-yellow-400" />
            Aktywacja Alertów
          </h2>
          <p className="text-sm text-gray-400">Wybierz typy alertów, które chcesz otrzymywać</p>
        </div>
        <span className="rounded-full bg-green-500/10 px-3 py-1 text-sm font-medium text-green-400">
          {activeCount} aktywnych
        </span>
      </div>

      {/* Sub-tabs: Marketplace / E-commerce */}
      <div className="flex gap-2">
        {(['marketplace', 'ecommerce'] as SubTab[]).map((t) => (
          <button
            key={t}
            onClick={() => setSubTab(t)}
            className={cn(
              'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              subTab === t
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            {t === 'marketplace' ? 'Marketplace' : 'E-commerce'}
          </button>
        ))}
      </div>

      {/* Alert type list */}
      <div className="space-y-2">
        {alertTypes.map(({ type, name, desc, icon: Icon }) => {
          const config = getConfig(type)
          const isEnabled = config?.enabled ?? false
          const isPending = (createMutation.isPending || toggleMutation.isPending)

          return (
            <div
              key={type}
              className="flex items-center gap-4 rounded-xl border border-gray-800 bg-[#1A1A1A] p-4"
            >
              <div className={cn(
                'rounded-lg p-2',
                isEnabled ? 'bg-green-500/10' : 'bg-gray-800'
              )}>
                <Icon className={cn('h-5 w-5', isEnabled ? 'text-green-400' : 'text-gray-500')} />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{name}</p>
                <p className="text-xs text-gray-500 truncate">{desc}</p>
              </div>

              <button
                onClick={() => handleToggle(type, name)}
                disabled={isPending}
                className={cn(
                  'relative h-6 w-11 rounded-full transition-colors',
                  isEnabled ? 'bg-green-500' : 'bg-gray-700',
                  isPending && 'opacity-50'
                )}
              >
                {isPending ? (
                  <Loader2 className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 animate-spin text-white" />
                ) : (
                  <span
                    className={cn(
                      'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                      isEnabled ? 'left-[22px]' : 'left-0.5'
                    )}
                  />
                )}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
