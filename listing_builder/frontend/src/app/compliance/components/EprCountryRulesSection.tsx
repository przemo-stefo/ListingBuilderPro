// frontend/src/app/compliance/components/EprCountryRulesSection.tsx
// Purpose: Cross-border EPR compliance — country cards with rules, thresholds, registration links
// NOT for: SP-API EPR report data (that's EprTab.tsx)

'use client'

import { useState } from 'react'
import {
  Globe,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Loader2,
  ShieldCheck,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEprCountryRules } from '@/lib/hooks/useEpr'
import type { EprCountryRule } from '@/lib/types'

// WHY: Flag emojis for visual country identification — no external deps needed
const COUNTRY_FLAGS: Record<string, string> = {
  DE: '\u{1F1E9}\u{1F1EA}',
  FR: '\u{1F1EB}\u{1F1F7}',
  ES: '\u{1F1EA}\u{1F1F8}',
  IT: '\u{1F1EE}\u{1F1F9}',
  SE: '\u{1F1F8}\u{1F1EA}',
  NL: '\u{1F1F3}\u{1F1F1}',
  PL: '\u{1F1F5}\u{1F1F1}',
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  packaging: { label: 'Opakowania', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  weee: { label: 'WEEE', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  batteries: { label: 'Baterie', color: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
}

// WHY: Group flat rules array into {DE: [...], FR: [...], ...} for card rendering
function groupByCountry(rules: EprCountryRule[]): Record<string, EprCountryRule[]> {
  const grouped: Record<string, EprCountryRule[]> = {}
  for (const rule of rules) {
    if (!grouped[rule.country_code]) grouped[rule.country_code] = []
    grouped[rule.country_code].push(rule)
  }
  return grouped
}

export default function EprCountryRulesSection() {
  const { data, isLoading } = useEprCountryRules()
  const [expandedCountry, setExpandedCountry] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-500" />
      </div>
    )
  }

  const rules = data?.rules ?? []
  if (rules.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-gray-500">
        Brak danych o regulacjach EPR. Uruchom migracje bazy danych.
      </div>
    )
  }

  const grouped = groupByCountry(rules)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <Globe className="h-4 w-4 text-gray-400" />
        <h3 className="text-sm font-semibold text-white">
          Regulacje EPR wg kraju ({Object.keys(grouped).length} krajow)
        </h3>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(grouped).map(([code, countryRules]) => (
          <CountryCard
            key={code}
            code={code}
            rules={countryRules}
            isExpanded={expandedCountry === code}
            onToggle={() => setExpandedCountry(expandedCountry === code ? null : code)}
          />
        ))}
      </div>
    </div>
  )
}

function CountryCard({
  code,
  rules,
  isExpanded,
  onToggle,
}: {
  code: string
  rules: EprCountryRule[]
  isExpanded: boolean
  onToggle: () => void
}) {
  const countryName = rules[0].country_name
  const flag = COUNTRY_FLAGS[code] || ''

  return (
    <div className={cn(
      'rounded-xl border bg-[#1A1A1A] transition-colors',
      isExpanded ? 'border-green-500/30 col-span-full' : 'border-gray-800 hover:border-gray-700'
    )}>
      {/* Header — always visible */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{flag}</span>
          <div>
            <p className="font-medium text-white">{countryName}</p>
            <p className="text-xs text-gray-500">{code} — {rules.length} kategorie</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {rules.map((r) => {
            const cat = CATEGORY_LABELS[r.category] || { label: r.category, color: 'bg-gray-500/10 text-gray-400' }
            return (
              <span key={r.category} className={cn('rounded px-2 py-0.5 text-[10px] font-medium border', cat.color)}>
                {cat.label}
              </span>
            )
          })}
          {isExpanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
        </div>
      </button>

      {/* Expanded detail */}
      {isExpanded && (
        <div className="border-t border-gray-800 px-4 pb-4 pt-3 space-y-4">
          {rules.map((rule) => (
            <RuleDetail key={rule.id} rule={rule} />
          ))}
        </div>
      )}
    </div>
  )
}

function RuleDetail({ rule }: { rule: EprCountryRule }) {
  const cat = CATEGORY_LABELS[rule.category] || { label: rule.category, color: '' }

  return (
    <div className="rounded-lg border border-gray-800 bg-[#121212] p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-green-400" />
          <span className="text-sm font-medium text-white">{cat.label}</span>
        </div>
        {rule.authority_url && (
          <a
            href={rule.authority_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
          >
            {rule.authority_name || 'Rejestracja'}
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>

      {/* Key info grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {rule.threshold_description && (
          <div className="col-span-2">
            <p className="text-gray-500">Prog</p>
            <p className="text-gray-300">{rule.threshold_description}</p>
          </div>
        )}
        {rule.deadline && (
          <div>
            <p className="text-gray-500">Termin</p>
            <p className="text-gray-300">{rule.deadline}</p>
          </div>
        )}
        {rule.penalty_description && (
          <div>
            <p className="text-gray-500">Kary</p>
            <p className="text-yellow-400 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 shrink-0" />
              {rule.penalty_description}
            </p>
          </div>
        )}
      </div>

      {/* Notes */}
      {rule.notes && (
        <p className="text-xs text-gray-500 leading-relaxed">{rule.notes}</p>
      )}
    </div>
  )
}
