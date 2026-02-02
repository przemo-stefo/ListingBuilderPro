// frontend/src/app/api/settings/route.ts
// Purpose: Mock settings API with mutable state (persists during dev session)
// NOT for: Production use — will be replaced by real backend

import { NextResponse } from 'next/server'
import type { SettingsResponse } from '@/lib/types'

// WHY: Module-level state so changes persist across requests during dev
let settingsState: SettingsResponse = {
  general: {
    store_name: 'My Marketplace Store',
    default_marketplace: 'amazon',
    timezone: 'America/New_York',
  },
  marketplace_connections: [
    {
      id: 'amazon',
      name: 'Amazon',
      connected: true,
      api_key: '****-****-****-1234',
      last_synced: '2026-01-30T14:30:00Z',
    },
    {
      id: 'ebay',
      name: 'eBay',
      connected: true,
      api_key: '****-****-****-5678',
      last_synced: '2026-01-29T10:15:00Z',
    },
    {
      id: 'walmart',
      name: 'Walmart',
      connected: false,
      api_key: '',
      last_synced: null,
    },
    {
      id: 'shopify',
      name: 'Shopify',
      connected: true,
      api_key: '****-****-****-9012',
      last_synced: '2026-01-28T08:45:00Z',
    },
    {
      id: 'allegro',
      name: 'Allegro',
      connected: false,
      api_key: '',
      last_synced: null,
    },
  ],
  notifications: {
    email_alerts: true,
    low_stock_alerts: true,
    competitor_price_changes: false,
    compliance_warnings: true,
  },
  data_export: {
    default_export_format: 'csv',
    auto_sync_frequency: '6h',
  },
}

export async function GET() {
  return NextResponse.json(settingsState)
}

export async function PUT(request: Request) {
  const payload = await request.json()

  // WHY: Merge each section individually so partial updates work
  if (payload.general) {
    settingsState.general = { ...settingsState.general, ...payload.general }
  }

  if (payload.marketplace_connections) {
    settingsState.marketplace_connections = payload.marketplace_connections
  }

  if (payload.notifications) {
    settingsState.notifications = {
      ...settingsState.notifications,
      ...payload.notifications,
    }
  }

  if (payload.data_export) {
    settingsState.data_export = {
      ...settingsState.data_export,
      ...payload.data_export,
    }
  }

  return NextResponse.json(settingsState)
}
