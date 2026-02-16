// frontend/src/app/compliance/page.tsx
// Purpose: Tab orchestrator for the Compliance Guard dashboard (7 tabs)
// NOT for: Individual tab logic (those are in components/), tab navigation (that's in Sidebar)

'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Shield } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'
import DashboardTab from './components/DashboardTab'
import AlertSettingsTab from './components/AlertSettingsTab'
import AlertsTab from './components/AlertsTab'
import IntegrationsTab from './components/IntegrationsTab'
import UploadTab from './components/UploadTab'
import EprTab from './components/EprTab'
import AuditTab from './components/AuditTab'

type Tab = 'dashboard' | 'audit' | 'settings' | 'alerts' | 'integrations' | 'upload' | 'epr'

const validTabs = new Set<string>(['dashboard', 'audit', 'settings', 'alerts', 'integrations', 'upload', 'epr'])

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
      {/* Header — tabs moved to sidebar */}
      <div className="flex items-center gap-3">
        <Shield className="h-6 w-6 text-green-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">Compliance Guard</h1>
          <p className="text-sm text-gray-400">
            Monitoruj zgodność produktów na wszystkich marketplace
          </p>
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'dashboard' && <DashboardTab onNavigate={(tab) => setActiveTab(tab as Tab)} />}
      {activeTab === 'audit' && <AuditTab />}
      {activeTab === 'settings' && <AlertSettingsTab />}
      {activeTab === 'alerts' && <AlertsTab />}
      {activeTab === 'integrations' && <IntegrationsTab />}
      {activeTab === 'upload' && <UploadTab />}
      {activeTab === 'epr' && <EprTab />}

      <FaqSection
        title="FAQ — Compliance Guard"
        subtitle="Najczesciej zadawane pytania o monitorowaniu zgodnosci"
        items={[
          { question: 'Co to jest Compliance Guard?', answer: 'System monitorowania zgodnosci produktow z regulacjami UE i marketplace. Sledzi zmiany w przepisach (GPSR, EPR, CE, REACH) i ostrzega Cie zanim Twoje oferty zostana zablokowane.' },
          { question: 'Jakie regulacje monitoruje?', answer: 'GPSR (bezpieczenstwo produktow), EPR (rozszerzona odpowiedzialnosc producenta), oznaczenia CE, REACH (substancje chemiczne), regulacje marketplace (Amazon, eBay, Kaufland, Allegro) i wiele wiecej.' },
          { question: 'Jak dzialaja alerty?', answer: 'Wlacz alerty w zakladce "Aktywacja Alertow" — wybierz typy regulacji i marketplace. System sprawdza zmiany co 24h i wysyla powiadomienia email/webhook gdy wykryje nowe wymagania lub deadline.' },
          { question: 'Co to sa raporty EPR?', answer: 'EPR (Extended Producer Responsibility) wymaga rejestracji i raportowania opakowan w kazdym kraju UE. Zakladka "Raporty EPR" pomaga generowac wymagane raporty na podstawie danych z Twojego konta sprzedawcy.' },
        ]}
      />
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
