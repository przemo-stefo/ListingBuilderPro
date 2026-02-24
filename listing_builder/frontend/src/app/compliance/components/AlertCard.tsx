// frontend/src/app/compliance/components/AlertCard.tsx
// Purpose: Single alert card with expandable details, action steps, and acknowledge button
// NOT for: Alert list layout or filtering (that's AlertsTab)

'use client'

import { useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Loader2,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
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

interface AlertCardProps {
  alert: MonitoringAlert
  onAcknowledge: () => void
  isAcknowledging: boolean
  isResolved: boolean
}

export default function AlertCard({ alert, onAcknowledge, isAcknowledging, isResolved }: AlertCardProps) {
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
      isResolved
        ? 'border-gray-800 opacity-70'
        : isCritical ? 'border-red-500/30' : 'border-yellow-500/20'
    )}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-4 p-4 text-left"
      >
        {isResolved ? (
          <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0" />
        ) : isCritical ? (
          <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={cn(
              'rounded px-2 py-0.5 text-[10px] font-bold uppercase',
              isResolved
                ? 'bg-green-500/10 text-green-400'
                : isCritical ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
            )}>
              {isResolved ? 'ROZWIĄZANY' : isCritical ? 'WYSOKIE RYZYKO' : 'UWAGA'}
            </span>
            <span className="text-[10px] text-gray-500 uppercase">{alert.alert_type.replace(/_/g, ' ')}</span>
          </div>
          <p className="text-sm font-medium text-white truncate">{alert.title}</p>
          <p className="text-xs text-gray-500 truncate">{alert.message}</p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {/* WHY: Show resolved date for acknowledged alerts, days left for active ones */}
          {isResolved ? (
            <span className="text-xs text-gray-500">
              {new Date(alert.acknowledged_at ?? alert.triggered_at).toLocaleDateString('pl-PL')}
            </span>
          ) : daysLeft > 0 ? (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="h-3 w-3" />
              {daysLeft}d
            </span>
          ) : null}
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
            {isResolved && alert.acknowledged_at && (
              <div>
                <span className="text-gray-500">Rozwiązano: </span>
                <span className="text-white">{new Date(alert.acknowledged_at).toLocaleString('pl-PL')}</span>
              </div>
            )}
          </div>

          {/* Action steps — only for unresolved alerts */}
          {!isResolved && (
            <>
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
            </>
          )}
        </div>
      )}
    </div>
  )
}
