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
} from 'lucide-react'

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

const navItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Products',
    href: '/products',
    icon: Package,
  },
  {
    title: 'Import',
    href: '/products/import',
    icon: Upload,
  },
  {
    title: 'Optimize',
    href: '/optimize',
    icon: Sparkles,
  },
  {
    title: 'Expert Q&A',
    href: '/expert-qa',
    icon: Brain,
  },
  {
    title: 'Converter',
    href: '/converter',
    icon: ArrowRightLeft,
  },
  {
    title: 'Wiadomości',
    href: '/news',
    icon: Newspaper,
  },
  {
    title: 'Manager Ofert',
    href: '/allegro-manager',
    icon: Store,
    premiumOnly: true,
  },
  {
    title: 'Monitoring',
    href: '/monitoring',
    icon: Activity,
    premiumOnly: true,
  },
  {
    title: 'Publish',
    href: '/publish',
    icon: Send,
  },
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
      <div className="mb-8">
        <h1 className="text-xl font-bold text-white">
          Marketplace Listing
        </h1>
        <p className="text-sm text-gray-400">Automation System</p>
      </div>

      <nav className="space-y-1 flex-1 overflow-y-auto">
        {navItems.map((item) => {
          const basePath = item.href.split('?')[0]
          const isActive = pathname === basePath && !item.href.includes('?')
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
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

        {/* WHY: Compliance as expandable section — sub-tabs shown inline in sidebar */}
        <div>
          <button
            onClick={() => setComplianceOpen(!complianceOpen)}
            className={cn(
              'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
              isOnCompliance
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            )}
          >
            <Shield className="h-4 w-4" />
            Compliance
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
      </nav>

      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-center">
          <TierBadge tier={tier} size="md" />
        </div>
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
          <p className="text-xs text-gray-400">
            API Status
          </p>
          <p className="text-xs font-mono text-green-500">
            {/* WHY: Show environment, not raw URL — avoids exposing backend address */}
            {process.env.NODE_ENV === 'production' ? 'Production' : 'Development'}
          </p>
        </div>
      </div>
    </div>
  )
}
