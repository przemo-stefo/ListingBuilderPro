// frontend/src/app/compliance/page.tsx
// Purpose: Tab orchestrator for the Compliance Guard dashboard (5 tabs)
// NOT for: Individual tab logic (those are in components/)

'use client'

import { useState } from 'react'
import {
  Shield,
  BarChart3,
  Bell,
  AlertTriangle,
  Link2,
  Upload,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import DashboardTab from './components/DashboardTab'
import AlertSettingsTab from './components/AlertSettingsTab'
import AlertsTab from './components/AlertsTab'
import IntegrationsTab from './components/IntegrationsTab'
import UploadTab from './components/UploadTab'

type Tab = 'dashboard' | 'settings' | 'alerts' | 'integrations' | 'upload'

const tabs: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'dashboard', label: 'Panel Główny', icon: BarChart3 },
  { key: 'settings', label: 'Aktywacja Alertów', icon: Bell },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle },
  { key: 'integrations', label: 'Integracje', icon: Link2 },
  { key: 'upload', label: 'Upload', icon: Upload },
]

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')

  return (
    <div className="space-y-6">
      {/* Header + tabs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-6 w-6 text-green-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Compliance Guard</h1>
            <p className="text-sm text-gray-400">
              Monitoruj zgodność produktów na wszystkich marketplace
            </p>
          </div>
        </div>

        {/* WHY: Horizontal scrollable tabs for mobile */}
        <div className="flex overflow-x-auto rounded-lg border border-gray-800 p-1">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                'flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-1.5 text-sm transition-colors',
                activeTab === key
                  ? 'bg-white/10 text-white'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'dashboard' && <DashboardTab onNavigate={(tab) => setActiveTab(tab as Tab)} />}
      {activeTab === 'settings' && <AlertSettingsTab />}
      {activeTab === 'alerts' && <AlertsTab />}
      {activeTab === 'integrations' && <IntegrationsTab />}
      {activeTab === 'upload' && <UploadTab />}
    </div>
  )
}
