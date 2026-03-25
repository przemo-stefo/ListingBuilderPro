// frontend/src/app/catalog-health/page.tsx
// Purpose: Catalog Health Check page — tab orchestrator for Dashboard/Scan/Issues
// NOT for: Individual tab logic (those are in components/)

'use client'

import { useState } from 'react'
import { BarChart3, Search, AlertTriangle, Stethoscope } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FeatureGate } from '@/components/tier/FeatureGate'
import DashboardTab from './components/DashboardTab'
import ScanTab from './components/ScanTab'
import IssuesTab from './components/IssuesTab'

type Tab = 'dashboard' | 'scan' | 'issues'

const NAV_TABS: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { key: 'scan', label: 'Skanuj', icon: Search },
]

export default function CatalogHealthPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  // WHY: Issues tab is navigated to from ScanTab with a specific scanId
  const [issuesScanId, setIssuesScanId] = useState<string | null>(null)

  const handleViewIssues = (scanId: string) => {
    setIssuesScanId(scanId)
    setActiveTab('issues')
  }

  const handleBackFromIssues = () => {
    setActiveTab('scan')
    setIssuesScanId(null)
  }

  return (
    <FeatureGate mode="redirect" redirectTo="/">
      <div className="space-y-6">
        {/* Header + tabs */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-emerald-500/20 p-2">
              <Stethoscope className="h-6 w-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Catalog Health Check</h1>
              <p className="text-sm text-gray-400">
                Skanuj katalog Amazon, wykrywaj problemy i naprawiaj jednym kliknieciem
              </p>
            </div>
          </div>

          {activeTab !== 'issues' && (
            <div className="flex rounded-lg border border-gray-800 p-1">
              {NAV_TABS.map(({ key, label, icon: Icon }) => (
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
          )}
        </div>

        {/* Tab content */}
        {activeTab === 'dashboard' && <DashboardTab />}
        {activeTab === 'scan' && <ScanTab onViewIssues={handleViewIssues} />}
        {activeTab === 'issues' && issuesScanId && (
          <IssuesTab scanId={issuesScanId} onBack={handleBackFromIssues} />
        )}
      </div>
    </FeatureGate>
  )
}
