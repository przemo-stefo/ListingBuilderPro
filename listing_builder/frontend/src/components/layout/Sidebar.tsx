// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar with links to all pages + tier badge
// NOT for: Page content or complex routing logic

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { TierBadge } from '@/components/tier/TierBadge'
import {
  LayoutDashboard,
  Package,
  Upload,
  ArrowRightLeft,
  Sparkles,
  Send,
  Shield,
  Activity,
  Brain,
  Crown,
  Newspaper,
  ChevronDown,
  BarChart3,
  Search,
  Bell,
  AlertTriangle,
  Link2,
  FileBarChart,
  Store,
  Key,
  List,
  TrendingUp,
  Warehouse,
  Users,
  Settings,
} from 'lucide-react'

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  premiumOnly?: boolean
}

interface NavSection {
  label: string
  items: NavItem[]
}

// WHY: Grouped by seller journey — Allegro seller expanding to Amazon:
// 1. Manage existing Allegro offers
// 2. Optimize listings with AI for new marketplace
// 3. Convert & publish to Amazon/eBay/Kaufland
// 4. Track performance across all marketplaces
const navSections: NavSection[] = [
  {
    label: 'Produkty',
    items: [
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard },
      { title: 'Produkty', href: '/products', icon: Package },
      { title: 'Import', href: '/products/import', icon: Upload },
      { title: 'Magazyn', href: '/inventory', icon: Warehouse },
    ],
  },
  {
    label: 'Allegro',
    items: [
      { title: 'Manager Ofert', href: '/allegro-manager', icon: Store, premiumOnly: true },
      { title: 'Allegro → Amazon', href: '/converter', icon: ArrowRightLeft },
    ],
  },
  {
    label: 'Optymalizacja AI',
    items: [
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles },
      { title: 'Słowa kluczowe', href: '/keywords', icon: Key },
      { title: 'Ekspert AI', href: '/expert-qa', icon: Brain },
    ],
  },
  {
    label: 'Sprzedaż',
    items: [
      { title: 'Publikuj', href: '/publish', icon: Send },
      { title: 'Listingi', href: '/listings', icon: List },
    ],
  },
  {
    label: 'Analityka',
    items: [
      { title: 'Analityka', href: '/analytics', icon: TrendingUp },
      { title: 'Konkurencja', href: '/competitors', icon: Users },
      { title: 'Monitoring', href: '/monitoring', icon: Activity, premiumOnly: true },
      { title: 'Wiadomości', href: '/news', icon: Newspaper },
    ],
  },
]

// WHY: Compliance sub-tabs defined here so sidebar shows them as expandable menu
const complianceSubItems = [
  { key: 'dashboard', label: 'Panel Główny', icon: BarChart3 },
  { key: 'audit', label: 'Audyt', icon: Search },
  { key: 'settings', label: 'Aktywacja Alertów', icon: Bell },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle },
  { key: 'integrations', label: 'Integracje', icon: Link2 },
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'epr', label: 'Raporty EPR', icon: FileBarChart },
]

export function Sidebar() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { tier } = useTier()

  // WHY: Auto-expand when user is on /compliance, collapse otherwise
  const isOnCompliance = pathname === '/compliance'
  const [complianceOpen, setComplianceOpen] = useState(isOnCompliance)
  const activeComplianceTab = searchParams.get('tab') || 'dashboard'

  return (
    <div className="w-64 border-r border-gray-800 bg-[#121212] p-6 flex flex-col">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">
          Marketplace Listing
        </h1>
        <p className="text-sm text-gray-400">Automation System</p>
      </div>

      <nav className="flex-1 overflow-y-auto space-y-4">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const basePath = item.href.split('?')[0]
                const isActive = pathname === basePath
                const Icon = item.icon

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
                      isActive
                        ? 'bg-white text-black'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.title}
                    {item.premiumOnly && tier !== 'premium' && (
                      <Crown className="h-3 w-3 text-amber-400 ml-auto" />
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}

        {/* WHY: Compliance as expandable section — sub-tabs shown inline in sidebar */}
        <div>
          <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
            Compliance
          </p>
          <button
            onClick={() => setComplianceOpen(!complianceOpen)}
            className={cn(
              'flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
              isOnCompliance
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            )}
          >
            <Shield className="h-4 w-4" />
            Compliance Guard
            <ChevronDown
              className={cn(
                'ml-auto h-4 w-4 transition-transform',
                complianceOpen && 'rotate-180'
              )}
            />
          </button>

          {complianceOpen && (
            <div className="ml-3 mt-1 space-y-0.5 border-l border-gray-800 pl-3">
              {complianceSubItems.map(({ key, label, icon: SubIcon }) => {
                const isSubActive = isOnCompliance && activeComplianceTab === key
                return (
                  <Link
                    key={key}
                    href={`/compliance?tab=${key}`}
                    className={cn(
                      'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-xs transition-colors',
                      isSubActive
                        ? 'bg-white/10 text-white'
                        : 'text-gray-500 hover:bg-gray-800/50 hover:text-gray-300'
                    )}
                  >
                    <SubIcon className="h-3.5 w-3.5" />
                    {label}
                  </Link>
                )
              })}
            </div>
          )}
        </div>

        {/* WHY: Settings separated — not part of seller workflow, utility */}
        <div className="pt-2 border-t border-gray-800/50">
          <Link
            href="/settings"
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
              pathname === '/settings'
                ? 'bg-white text-black'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            )}
          >
            <Settings className="h-4 w-4" />
            Ustawienia
          </Link>
        </div>
      </nav>

      {/* Footer — tier badge + legal links */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-center">
          <TierBadge tier={tier} size="md" />
        </div>
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
          <p className="text-xs text-gray-400">
            API Status
          </p>
          <p className="text-xs font-mono text-green-500">
            {process.env.NODE_ENV === 'production' ? 'Production' : 'Development'}
          </p>
        </div>
        <div className="flex justify-center gap-3 text-[10px] text-gray-600">
          <Link href="/privacy" className="hover:text-gray-400 transition-colors">
            Prywatność
          </Link>
          <span>·</span>
          <Link href="/terms" className="hover:text-gray-400 transition-colors">
            Regulamin
          </Link>
        </div>
      </div>
    </div>
  )
}
