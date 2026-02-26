// frontend/src/app/monitoring/page.tsx
// Purpose: Monitoring page — tab orchestrator for Dashboard/Products/Alert Rules/Alerts
// NOT for: Individual tab logic (those are in components/)

'use client'

import { useState } from 'react'
import { BarChart3, Package, Bell, AlertTriangle, TrendingUp, Settings, GitCompareArrows } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FaqSection } from '@/components/ui/FaqSection'

const MONITORING_FAQ = [
  { question: 'Co monitoruje Monitoring?', answer: 'System sledzi zmiany cen, pozycji, opinii i dostepnosci Twoich produktow na marketplace. Gdy wykryje istotna zmiane, wysyla alert.' },
  { question: 'Jak dodac produkt do monitorowania?', answer: 'Przejdz do zakladki "Products" i kliknij "Add Product". Podaj ASIN lub URL produktu, a system zacznie go sledzic automatycznie.' },
  { question: 'Jak skonfigurowac reguly alertow?', answer: 'W zakladce "Alert Rules" ustaw progi — np. "alert gdy cena spadnie o 10%" lub "alert gdy pozycja spadnie ponizej #50". Alerty pojawia sie w zakladce "Alerts".' },
  { question: 'Co to sa Snapshots?', answer: 'Snapshots to migawki stanu produktu w danym momencie. System robi je automatycznie przy kazdym sprawdzeniu. Mozesz porownac stan obecny z historycznym.' },
]
import { FeatureGate } from '@/components/tier/FeatureGate'
import DashboardTab from './components/DashboardTab'
import TrackedProductsTab from './components/TrackedProductsTab'
import AlertRulesTab from './components/AlertRulesTab'
import AlertHistoryTab from './components/AlertHistoryTab'
import SnapshotsTab from './components/SnapshotsTab'
import AlertSettingsTab from './components/AlertSettingsTab'
import ListingChangesTab from './components/ListingChangesTab'

type Tab = 'dashboard' | 'products' | 'rules' | 'alerts' | 'snapshots' | 'alert-settings' | 'changes'

const tabs: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'products', label: 'Products', icon: Package },
  { key: 'rules', label: 'Alert Rules', icon: Bell },
  { key: 'alerts', label: 'Alerts', icon: AlertTriangle },
  { key: 'snapshots', label: 'Snapshots', icon: TrendingUp },
  { key: 'alert-settings', label: 'Alert Settings', icon: Settings },
  { key: 'changes', label: 'Zmiany', icon: GitCompareArrows },
]

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')

  return (
    <FeatureGate mode="redirect" redirectTo="/">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Monitoring & Alerts</h1>
            <p className="text-sm text-gray-400">
              Track products across marketplaces and get alerted on changes
            </p>
          </div>

          <div className="flex rounded-lg border border-gray-800 p-1">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
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

        {activeTab === 'dashboard' && <DashboardTab />}
        {activeTab === 'products' && <TrackedProductsTab />}
        {activeTab === 'rules' && <AlertRulesTab />}
        {activeTab === 'alerts' && <AlertHistoryTab />}
        {activeTab === 'snapshots' && <SnapshotsTab />}
        {activeTab === 'alert-settings' && <AlertSettingsTab />}
        {activeTab === 'changes' && <ListingChangesTab />}

        <FaqSection
          title="Najczesciej zadawane pytania"
          subtitle="Monitoring i alerty"
          items={MONITORING_FAQ}
        />
      </div>
    </FeatureGate>
  )
}
