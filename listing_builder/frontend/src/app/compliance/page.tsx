// frontend/src/app/compliance/page.tsx
// Purpose: Tab orchestrator for the Compliance Guard dashboard (6 tabs)
// NOT for: Individual tab logic (those are in components/)

'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Shield,
  BarChart3,
  Bell,
  AlertTriangle,
  Link2,
  Upload,
  Newspaper,
  FileBarChart,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import DashboardTab from './components/DashboardTab'
import AlertSettingsTab from './components/AlertSettingsTab'
import AlertsTab from './components/AlertsTab'
import IntegrationsTab from './components/IntegrationsTab'
import UploadTab from './components/UploadTab'
import NewsTab from './components/NewsTab'
import EprTab from './components/EprTab'

type Tab = 'dashboard' | 'settings' | 'alerts' | 'integrations' | 'upload' | 'news' | 'epr'

const tabs: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'dashboard', label: 'Panel Główny', icon: BarChart3 },
  { key: 'news', label: 'Wiadomości', icon: Newspaper },
  { key: 'settings', label: 'Aktywacja Alertów', icon: Bell },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle },
  { key: 'integrations', label: 'Integracje', icon: Link2 },
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'epr', label: 'Raporty EPR', icon: FileBarChart },
]

const validTabs = new Set(tabs.map(t => t.key))

// WHY: Separate component — useSearchParams requires Suspense boundary in Next.js 14
function ComplianceContent() {
  const searchParams = useSearchParams()
  const tabFromUrl = searchParams.get('tab') as Tab | null
  const initialTab = tabFromUrl && validTabs.has(tabFromUrl) ? tabFromUrl : 'dashboard'
  const [activeTab, setActiveTab] = useState<Tab>(initialTab)

  // WHY: Sync tab when URL changes (e.g. sidebar click on "Wiadomości")
  useEffect(() => {
    if (tabFromUrl && validTabs.has(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [tabFromUrl])

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
      {activeTab === 'news' && <NewsTab />}
      {activeTab === 'settings' && <AlertSettingsTab />}
      {activeTab === 'alerts' && <AlertsTab />}
      {activeTab === 'integrations' && <IntegrationsTab />}
      {activeTab === 'upload' && <UploadTab />}
      {activeTab === 'epr' && <EprTab />}
    </div>
  )
}

export default function CompliancePage() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-lg bg-[#1A1A1A]" />}>
      <ComplianceContent />
    </Suspense>
  )
}
