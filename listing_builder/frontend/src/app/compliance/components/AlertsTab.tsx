// frontend/src/app/compliance/components/AlertsTab.tsx
// Purpose: Active alerts view — severity badges, action steps, acknowledge button
// NOT for: Alert configuration (that's AlertSettingsTab)

'use client'

import { useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Loader2,
  Bell,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlerts, useAcknowledgeAlert } from '@/lib/hooks/useMonitoring'
import type { MonitoringAlert } from '@/lib/types'

// WHY: Map alert_type to actionable steps the seller should take
const ACTION_STEPS: Record<string, string[]> = {
  price_change: [
    'Sprawdź aktualną cenę na marketplace',
    'Porównaj z cenami konkurencji',
    'Zdecyduj czy dostosować cenę',
  ],
  buy_box_lost: [
    'Sprawdź kto przejął Buy Box',
    'Zweryfikuj swoją cenę i warunki wysyłki',
    'Rozważ obniżenie ceny lub poprawę metryk',
  ],
  low_stock: [
    'Sprawdź aktualny stan magazynowy',
    'Złóż zamówienie uzupełniające',
    'Rozważ tymczasowe podniesienie ceny',
  ],
  listing_deactivated: [
    'Sprawdź powód dezaktywacji w Seller Central',
    'Popraw problematyczne pola w ofercie',
    'Złóż apelację jeśli to błąd platformy',
  ],
  compliance_fail: [
    'Przejrzyj raport compliance',
    'Uzupełnij brakującą dokumentację',
    'Zaktualizuj dane produktu na marketplace',
  ],
  return_spike: [
    'Przeanalizuj powody zwrotów',
    'Sprawdź jakość ostatnich dostaw',
    'Zaktualizuj opis produktu jeśli jest mylący',
  ],
  negative_review: [
    'Przeczytaj treść opinii',
    'Odpowiedz profesjonalnie na recenzję',
    'Rozwiąż problem klienta jeśli to możliwe',
  ],
}

const DEFAULT_ACTIONS = [
  'Sprawdź szczegóły alertu',
  'Podejmij odpowiednie działanie',
  'Oznacz alert jako rozwiązany',
]

export default function AlertsTab() {
  const alertsQuery = useAlerts()
  const ackMutation = useAcknowledgeAlert()

  const alerts = (alertsQuery.data?.items ?? []) as MonitoringAlert[]
  const unacknowledged = alerts.filter((a) => !a.acknowledged)
  const criticalCount = unacknowledged.filter((a) => a.severity === 'critical').length
  const warningCount = unacknowledged.filter((a) => a.severity === 'warning').length

  if (alertsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with counts */}
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Bell className="h-5 w-5 text-red-400" />
          Aktywne Alerty
        </h2>
        <div className="flex gap-2">
          {criticalCount > 0 && (
            <span className="rounded-full bg-red-500/10 px-3 py-0.5 text-xs font-medium text-red-400">
              {criticalCount} krytycznych
            </span>
          )}
          {warningCount > 0 && (
            <span className="rounded-full bg-yellow-500/10 px-3 py-0.5 text-xs font-medium text-yellow-400">
              {warningCount} ostrzeżeń
            </span>
          )}
        </div>
      </div>

      {unacknowledged.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-10 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-green-400 mb-3" />
          <p className="text-white font-medium">Brak aktywnych alertów</p>
          <p className="text-sm text-gray-500 mt-1">Wszystko wygląda dobrze!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {unacknowledged.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={() => ackMutation.mutate(alert.id)}
              isAcknowledging={ackMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* Acknowledged (resolved) alerts */}
      {alerts.some((a) => a.acknowledged) && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-gray-400">Rozwiązane</h3>
          <div className="space-y-2 opacity-60">
            {alerts
              .filter((a) => a.acknowledged)
              .slice(0, 5)
              .map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center gap-3 rounded-lg border border-gray-800 bg-[#1A1A1A] p-3"
                >
                  <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />
                  <span className="text-sm text-gray-400 truncate flex-1">{alert.title}</span>
                  <span className="text-xs text-gray-600">
                    {new Date(alert.acknowledged_at ?? alert.triggered_at).toLocaleDateString('pl-PL')}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

function AlertCard({
  alert,
  onAcknowledge,
  isAcknowledging,
}: {
  alert: MonitoringAlert
  onAcknowledge: () => void
  isAcknowledging: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const isCritical = alert.severity === 'critical'
  const actions = ACTION_STEPS[alert.alert_type] ?? DEFAULT_ACTIONS

  // WHY: Estimate "days to act" — 3 for critical, 7 for warning
  const daysToAct = isCritical ? 3 : 7
  const daysSince = Math.floor(
    (Date.now() - new Date(alert.triggered_at).getTime()) / (1000 * 60 * 60 * 24)
  )
  const daysLeft = Math.max(0, daysToAct - daysSince)

  return (
    <div className={cn(
      'rounded-xl border bg-[#1A1A1A] overflow-hidden',
      isCritical ? 'border-red-500/30' : 'border-yellow-500/20'
    )}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-4 p-4 text-left"
      >
        {isCritical ? (
          <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={cn(
              'rounded px-2 py-0.5 text-[10px] font-bold uppercase',
              isCritical ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
            )}>
              {isCritical ? 'WYSOKIE RYZYKO' : 'UWAGA'}
            </span>
            <span className="text-[10px] text-gray-500 uppercase">{alert.alert_type.replace(/_/g, ' ')}</span>
          </div>
          <p className="text-sm font-medium text-white truncate">{alert.title}</p>
          <p className="text-xs text-gray-500 truncate">{alert.message}</p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {daysLeft > 0 && (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="h-3 w-3" />
              {daysLeft}d
            </span>
          )}
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-800 bg-[#121212] p-4 space-y-4">
          {/* Alert details */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {alert.details?.product_id != null && (
              <div>
                <span className="text-gray-500">Produkt: </span>
                <span className="text-white font-mono">{String(alert.details.product_id)}</span>
              </div>
            )}
            {alert.details?.marketplace != null && (
              <div>
                <span className="text-gray-500">Marketplace: </span>
                <span className="text-white capitalize">{String(alert.details.marketplace)}</span>
              </div>
            )}
            <div>
              <span className="text-gray-500">Wykryto: </span>
              <span className="text-white">{new Date(alert.triggered_at).toLocaleString('pl-PL')}</span>
            </div>
          </div>

          {/* Action steps */}
          <div>
            <p className="text-xs font-semibold text-white mb-2 uppercase tracking-wide">
              Co zrobić teraz
            </p>
            <ol className="space-y-1.5">
              {actions.map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-800 text-[10px] text-gray-400">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          <button
            onClick={(e) => { e.stopPropagation(); onAcknowledge() }}
            disabled={isAcknowledging}
            className={cn(
              'w-full rounded-lg py-2 text-sm font-medium transition-colors',
              isCritical
                ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                : 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20'
            )}
          >
            {isAcknowledging ? (
              <Loader2 className="mx-auto h-4 w-4 animate-spin" />
            ) : (
              'Rozwiąż problem'
            )}
          </button>
        </div>
      )}
    </div>
  )
}
