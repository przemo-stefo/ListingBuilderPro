// frontend/src/app/settings/page.tsx
// Purpose: Settings page with 4 sections — General, Marketplaces, Notifications, Data & Export
// NOT for: API logic or data fetching (handled by hooks/useSettings.ts)

'use client'

import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Link, Bell, Download, Save } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSettings, useUpdateSettings } from '@/lib/hooks/useSettings'
import type {
  MarketplaceId,
  MarketplaceConnection,
  NotificationSettings,
  ExportFormat,
  SyncFrequency,
} from '@/lib/types'

const MARKETPLACE_OPTIONS: { id: MarketplaceId; label: string }[] = [
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'walmart', label: 'Walmart' },
  { id: 'shopify', label: 'Shopify' },
  { id: 'allegro', label: 'Allegro' },
]

const TIMEZONE_OPTIONS = [
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Warsaw',
]

const EXPORT_OPTIONS: { id: ExportFormat; label: string }[] = [
  { id: 'csv', label: 'CSV' },
  { id: 'json', label: 'JSON' },
  { id: 'excel', label: 'Excel' },
]

const SYNC_OPTIONS: { id: SyncFrequency; label: string }[] = [
  { id: 'manual', label: 'Manual' },
  { id: '1h', label: '1h' },
  { id: '6h', label: '6h' },
  { id: '12h', label: '12h' },
  { id: '24h', label: '24h' },
]

// WHY: Skeleton shows while data loads — same pattern as other pages
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="h-48 animate-pulse rounded-lg border border-gray-800 bg-[#121212]"
        />
      ))}
    </div>
  )
}

export default function SettingsPage() {
  const { data, isLoading, isError, refetch } = useSettings()
  const updateSettings = useUpdateSettings()

  // Local state for each section (populated from server data)
  const [storeName, setStoreName] = useState('')
  const [defaultMarketplace, setDefaultMarketplace] = useState<MarketplaceId>('amazon')
  const [timezone, setTimezone] = useState('America/New_York')
  const [connections, setConnections] = useState<MarketplaceConnection[]>([])
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email_alerts: true,
    low_stock_alerts: true,
    competitor_price_changes: false,
    compliance_warnings: true,
  })
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv')
  const [syncFrequency, setSyncFrequency] = useState<SyncFrequency>('6h')

  // WHY: Populate local state when server data arrives or changes
  useEffect(() => {
    if (!data) return
    setStoreName(data.general.store_name)
    setDefaultMarketplace(data.general.default_marketplace)
    setTimezone(data.general.timezone)
    setConnections(data.marketplace_connections)
    setNotifications(data.notifications)
    setExportFormat(data.data_export.default_export_format)
    setSyncFrequency(data.data_export.auto_sync_frequency)
  }, [data])

  if (isLoading) return <LoadingSkeleton />

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-gray-400">Failed to load settings</p>
        <Button variant="outline" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-gray-400">
          Manage your store configuration, marketplace connections, and preferences
        </p>
      </div>

      {/* Card 1 — General Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">General Settings</CardTitle>
          </div>
          <CardDescription>Basic store configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Store Name */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Store Name</label>
            <Input
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="Your store name"
            />
          </div>

          {/* Default Marketplace */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Default Marketplace</label>
            <div className="flex flex-wrap gap-2">
              {MARKETPLACE_OPTIONS.map((mp) => (
                <Button
                  key={mp.id}
                  variant={defaultMarketplace === mp.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setDefaultMarketplace(mp.id)}
                >
                  {mp.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Timezone */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Timezone</label>
            <div className="flex flex-wrap gap-2">
              {TIMEZONE_OPTIONS.map((tz) => (
                <Button
                  key={tz}
                  variant={timezone === tz ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimezone(tz)}
                >
                  {tz.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </div>

          {/* Save */}
          <div className="flex justify-end">
            <Button
              onClick={() =>
                updateSettings.mutate({
                  general: {
                    store_name: storeName,
                    default_marketplace: defaultMarketplace,
                    timezone,
                  },
                })
              }
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Card 2 — Marketplace Connections */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Link className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Marketplace Connections</CardTitle>
          </div>
          <CardDescription>Manage API connections to your marketplaces</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            {connections.map((conn, idx) => (
              <div
                key={conn.id}
                className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">{conn.name}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      conn.connected
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-700 text-gray-400'
                    }`}
                  >
                    {conn.connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>

                <Input
                  type="password"
                  value={conn.api_key}
                  onChange={(e) => {
                    const updated = [...connections]
                    updated[idx] = { ...updated[idx], api_key: e.target.value }
                    setConnections(updated)
                  }}
                  placeholder="Enter API key"
                />

                <Button
                  size="sm"
                  variant={conn.connected ? 'destructive' : 'default'}
                  className="w-full"
                  onClick={() => {
                    const updated = [...connections]
                    updated[idx] = {
                      ...updated[idx],
                      connected: !updated[idx].connected,
                      // WHY: Set last_synced when connecting
                      last_synced: !updated[idx].connected
                        ? new Date().toISOString()
                        : updated[idx].last_synced,
                    }
                    setConnections(updated)
                  }}
                >
                  {conn.connected ? 'Disconnect' : 'Connect'}
                </Button>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <Button
              onClick={() =>
                updateSettings.mutate({ marketplace_connections: connections })
              }
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Card 3 — Notification Preferences */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Notification Preferences</CardTitle>
          </div>
          <CardDescription>Choose which alerts you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {([
            {
              key: 'email_alerts' as const,
              label: 'Email Alerts',
              desc: 'Receive email notifications for important events',
            },
            {
              key: 'low_stock_alerts' as const,
              label: 'Low Stock Alerts',
              desc: 'Get notified when inventory drops below reorder point',
            },
            {
              key: 'competitor_price_changes' as const,
              label: 'Competitor Price Changes',
              desc: 'Alert when competitors change their pricing',
            },
            {
              key: 'compliance_warnings' as const,
              label: 'Compliance Warnings',
              desc: 'Notifications about listing compliance issues',
            },
          ]).map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] p-4"
            >
              <div>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-gray-400">{item.desc}</p>
              </div>
              <Button
                size="sm"
                variant={notifications[item.key] ? 'default' : 'outline'}
                onClick={() =>
                  setNotifications((prev) => ({
                    ...prev,
                    [item.key]: !prev[item.key],
                  }))
                }
              >
                {notifications[item.key] ? 'ON' : 'OFF'}
              </Button>
            </div>
          ))}

          <div className="flex justify-end">
            <Button
              onClick={() => updateSettings.mutate({ notifications })}
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Card 4 — Data & Export */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Data & Export</CardTitle>
          </div>
          <CardDescription>Configure export formats and sync schedule</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Export Format */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Export Format</label>
            <div className="flex gap-2">
              {EXPORT_OPTIONS.map((opt) => (
                <Button
                  key={opt.id}
                  variant={exportFormat === opt.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setExportFormat(opt.id)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Sync Frequency */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Auto-Sync Frequency</label>
            <div className="flex gap-2">
              {SYNC_OPTIONS.map((opt) => (
                <Button
                  key={opt.id}
                  variant={syncFrequency === opt.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSyncFrequency(opt.id)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Save */}
          <div className="flex justify-end">
            <Button
              onClick={() =>
                updateSettings.mutate({
                  data_export: {
                    default_export_format: exportFormat,
                    auto_sync_frequency: syncFrequency,
                  },
                })
              }
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
