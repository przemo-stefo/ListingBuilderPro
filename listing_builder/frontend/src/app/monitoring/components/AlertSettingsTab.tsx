// frontend/src/app/monitoring/components/AlertSettingsTab.tsx
// Purpose: Sellerboard-style alert settings table with categories, toggles, priorities
// NOT for: Alert history, dashboard stats, or product tracking

'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { ChevronDown, ChevronRight, Info, Loader2, Save, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlertSettings, useUpdateAlertSettings } from '@/lib/hooks/useAlertSettings'
import type { AlertSettingResponse, AlertTypeSettingPayload } from '@/lib/api/alertSettings'
import AlertSettingRow from './AlertSettingRow'

const CATEGORY_LABELS: Record<string, string> = {
  product: 'Product Alerts',
  financial: 'Financial Alerts',
  performance: 'Performance Alerts',
}

export default function AlertSettingsTab() {
  const { data: settings, isLoading, error } = useAlertSettings()
  const updateMutation = useUpdateAlertSettings()

  // WHY local state: User edits in-place, then clicks Save (bulk upsert)
  const [local, setLocal] = useState<AlertSettingResponse[]>([])
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    if (settings) setLocal(settings)
  }, [settings])

  const updateField = useCallback(
    (alertType: string, field: keyof AlertTypeSettingPayload, value: unknown) => {
      setLocal(prev =>
        prev.map(s => s.alert_type === alertType ? { ...s, [field]: value } : s)
      )
      setDirty(true)
    },
    []
  )

  const handleSave = () => {
    const payload: AlertTypeSettingPayload[] = local.map(s => ({
      alert_type: s.alert_type,
      priority: s.priority,
      notify_in_app: s.notify_in_app,
      notify_email: s.notify_email,
      email_recipients: s.email_recipients,
      enabled: s.enabled,
    }))
    updateMutation.mutate(payload, { onSuccess: () => setDirty(false) })
  }

  const grouped = useMemo(() => {
    const groups: Record<string, AlertSettingResponse[]> = {}
    for (const item of local) {
      if (!groups[item.category]) groups[item.category] = []
      groups[item.category].push(item)
    }
    return groups
  }, [local])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-900/50 bg-red-950/20 p-4">
        <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
        <p className="text-sm text-red-300">Failed to load alert settings. Please try again later.</p>
      </div>
    )
  }

  const activeCount = local.filter(s => s.active).length

  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="flex items-start gap-3 rounded-lg border border-gray-800 bg-gray-900/50 p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-400" />
        <div className="text-sm text-gray-300">
          <p>
            <strong>{activeCount} z {local.length}</strong> alert types are currently active (Keepa data).
            Types marked <span className="rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-500">SP-API</span> will
            activate once Amazon SP-API is connected.
          </p>
          <p className="mt-1 text-gray-500">Email delivery is coming soon. In-app notifications work now.</p>
        </div>
      </div>

      {/* Categories */}
      {['product', 'financial', 'performance'].map(cat => {
        const items = grouped[cat] || []
        const isCollapsed = collapsed[cat]

        return (
          <div key={cat} className="rounded-lg border border-gray-800 overflow-hidden">
            <button
              onClick={() => setCollapsed(prev => ({ ...prev, [cat]: !prev[cat] }))}
              className="flex w-full items-center gap-2 bg-gray-900/70 px-4 py-3 text-left"
            >
              {isCollapsed
                ? <ChevronRight className="h-4 w-4 text-gray-500" />
                : <ChevronDown className="h-4 w-4 text-gray-500" />}
              <span className="text-sm font-semibold text-white uppercase tracking-wide">
                {CATEGORY_LABELS[cat] || cat}
              </span>
              <span className="text-xs text-gray-500">({items.length})</span>
            </button>

            {/* WHY overflow-x-auto: prevents horizontal overflow on mobile */}
            {!isCollapsed && (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] text-sm">
                  <thead>
                    <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                      <th className="px-4 py-2 text-left font-medium w-[40%]">Alert Type</th>
                      <th className="px-4 py-2 text-left font-medium w-[15%]">Priority</th>
                      <th className="px-4 py-2 text-center font-medium w-[10%]">In-App</th>
                      <th className="px-4 py-2 text-center font-medium w-[10%]">Email</th>
                      <th className="px-4 py-2 text-left font-medium w-[25%]">Recipients</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map(item => (
                      <AlertSettingRow key={item.alert_type} item={item} onUpdate={updateField} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )
      })}

      {/* Save button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={!dirty || updateMutation.isPending}
          className={cn(
            'flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium transition-colors',
            dirty
              ? 'bg-blue-600 text-white hover:bg-blue-500'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          )}
        >
          {updateMutation.isPending
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <Save className="h-4 w-4" />}
          Save Changes
        </button>
      </div>
    </div>
  )
}
