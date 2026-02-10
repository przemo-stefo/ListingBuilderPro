// frontend/src/app/monitoring/page.tsx
// Purpose: Monitoring page — tab orchestrator for Dashboard/Products/Alert Rules/Alerts
// NOT for: Individual tab logic (those are in components/)

'use client'

import { useState } from 'react'
import { BarChart3, Package, Bell, AlertTriangle, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FeatureGate } from '@/components/tier/FeatureGate'
import DashboardTab from './components/DashboardTab'
import TrackedProductsTab from './components/TrackedProductsTab'
import AlertRulesTab from './components/AlertRulesTab'
import AlertHistoryTab from './components/AlertHistoryTab'
import TracesTab from './components/TracesTab'

type Tab = 'dashboard' | 'products' | 'rules' | 'alerts' | 'traces'

const tabs: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'products', label: 'Products', icon: Package },
  { key: 'rules', label: 'Alert Rules', icon: Bell },
  { key: 'alerts', label: 'Alerts', icon: AlertTriangle },
  { key: 'traces', label: 'Traces', icon: Activity },
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
        {activeTab === 'traces' && <TracesTab />}
      </div>
    </FeatureGate>
  )
}
