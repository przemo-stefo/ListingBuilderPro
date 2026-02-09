// frontend/src/app/monitoring/components/AlertRulesTab.tsx
// Purpose: CRUD for alert config rules (create/toggle/delete)
// NOT for: Alert history display or product tracking

'use client'

import { useState } from 'react'
import { useAlertConfigs, useCreateAlertConfig, useDeleteAlertConfig, useToggleAlertConfig } from '@/lib/hooks/useMonitoring'
import { Trash2, Power } from 'lucide-react'

const ALERT_TYPES = [
  'price_change',
  'buy_box_lost',
  'low_stock',
  'listing_deactivated',
  'negative_review',
  'return_spike',
  'compliance_fail',
] as const

const TYPE_COLORS: Record<string, string> = {
  price_change: 'border-yellow-700 text-yellow-400',
  buy_box_lost: 'border-red-700 text-red-400',
  low_stock: 'border-orange-700 text-orange-400',
  listing_deactivated: 'border-gray-600 text-gray-400',
  negative_review: 'border-red-700 text-red-400',
  return_spike: 'border-orange-700 text-orange-400',
  compliance_fail: 'border-red-700 text-red-400',
}

const MARKETPLACES = ['', 'allegro', 'amazon', 'kaufland', 'ebay'] as const

export default function AlertRulesTab() {
  const { data, isLoading } = useAlertConfigs()
  const createMutation = useCreateAlertConfig()
  const deleteMutation = useDeleteAlertConfig()
  const toggleMutation = useToggleAlertConfig()

  const [alertType, setAlertType] = useState<string>('price_change')
  const [name, setName] = useState('')
  const [threshold, setThreshold] = useState('')
  const [marketplace, setMarketplace] = useState('')
  const [cooldown, setCooldown] = useState(60)
  const [webhookUrl, setWebhookUrl] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    await createMutation.mutateAsync({
      alert_type: alertType,
      name: name.trim(),
      threshold: threshold ? Number(threshold) : undefined,
      marketplace: marketplace || undefined,
      cooldown_minutes: cooldown,
      webhook_url: webhookUrl.trim() || undefined,
    })

    setName('')
    setThreshold('')
    setWebhookUrl('')
  }

  return (
    <div className="space-y-6">
      {/* Create rule form */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
        <p className="mb-4 text-sm font-medium text-white">Create Alert Rule</p>
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            <select
              value={alertType}
              onChange={(e) => setAlertType(e.target.value)}
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
            >
              {ALERT_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
              ))}
            </select>

            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Rule name"
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
              required
            />

            <input
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder="Threshold (optional)"
              type="number"
              step="any"
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
            />

            <select
              value={marketplace}
              onChange={(e) => setMarketplace(e.target.value)}
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
            >
              <option value="">All marketplaces</option>
              {MARKETPLACES.filter(Boolean).map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <select
              value={cooldown}
              onChange={(e) => setCooldown(Number(e.target.value))}
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white"
            >
              {[5, 15, 30, 60, 120, 360, 1440].map((m) => (
                <option key={m} value={m}>{m} min cooldown</option>
              ))}
            </select>

            <input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="Webhook URL (optional)"
              className="rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-500"
            />

            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-gray-200 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Rule'}
            </button>
          </div>
        </form>
      </div>

      {/* Rules list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg border border-gray-800 bg-[#1A1A1A]" />
          ))}
        </div>
      ) : !data?.items.length ? (
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center text-sm text-gray-500">
          No alert rules configured. Create one above.
        </div>
      ) : (
        <div className="space-y-2">
          {data.items.map((config) => (
            <div
              key={config.id}
              className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] px-5 py-3"
            >
              <div className="flex items-center gap-4">
                <span className={`rounded-full border bg-white/5 px-2.5 py-0.5 text-xs ${TYPE_COLORS[config.alert_type] || 'border-gray-700 text-gray-400'}`}>
                  {config.alert_type.replace(/_/g, ' ')}
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{config.name}</p>
                  <p className="text-xs text-gray-500">
                    {config.threshold != null && `Threshold: ${config.threshold} · `}
                    {config.marketplace && `${config.marketplace} · `}
                    Cooldown: {config.cooldown_minutes}m
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleMutation.mutate(config.id)}
                  className={`rounded-md p-1.5 transition-colors ${
                    config.enabled
                      ? 'text-green-500 hover:bg-green-500/10'
                      : 'text-gray-600 hover:bg-gray-800'
                  }`}
                  title={config.enabled ? 'Disable' : 'Enable'}
                >
                  <Power className="h-4 w-4" />
                </button>

                <button
                  onClick={() => deleteMutation.mutate(config.id)}
                  className="rounded-md p-1.5 text-gray-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
