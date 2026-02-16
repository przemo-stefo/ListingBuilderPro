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
  Info,
} from 'lucide-react'

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  premiumOnly?: boolean
  // WHY: Tooltip description for clients who don't know what each tool does
  desc?: string
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
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard, desc: 'Przeglad statystyk i szybkie akcje' },
      { title: 'Produkty', href: '/products', icon: Package, desc: 'Lista wszystkich produktow w systemie' },
      { title: 'Import', href: '/products/import', icon: Upload, desc: 'Importuj produkty z CSV lub Allegro' },
      { title: 'Magazyn', href: '/inventory', icon: Warehouse, desc: 'Stany magazynowe i synchronizacja' },
    ],
  },
  {
    label: 'Allegro',
    items: [
      { title: 'Manager Ofert', href: '/allegro-manager', icon: Store, premiumOnly: true, desc: 'Zarzadzaj ofertami Allegro — edycja, ceny, masowe akcje' },
      { title: 'Allegro → Amazon', href: '/converter', icon: ArrowRightLeft, desc: 'Konwertuj oferty z Allegro na format Amazon' },
    ],
  },
  {
    label: 'Optymalizacja AI',
    items: [
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles, desc: 'AI generuje tytul, bullety, opis i slowa kluczowe backend' },
      { title: 'Slowa kluczowe', href: '/keywords', icon: Key, desc: 'Analiza i badanie slow kluczowych dla marketplace' },
      { title: 'Ekspert AI', href: '/expert-qa', icon: Brain, desc: 'Zadaj pytanie ekspertowi AI o sprzedazy na marketplace' },
    ],
  },
  {
    label: 'Sprzedaz',
    items: [
      { title: 'Publikuj', href: '/publish', icon: Send, desc: 'Opublikuj zoptymalizowane listingi na Amazon, eBay, Kaufland' },
      { title: 'Listingi', href: '/listings', icon: List, desc: 'Wszystkie opublikowane listingi i ich status' },
    ],
  },
  {
    label: 'Analityka',
    items: [
      { title: 'Analityka', href: '/analytics', icon: TrendingUp, desc: 'Wykresy sprzedazy i metryki wydajnosci' },
      { title: 'Konkurencja', href: '/competitors', icon: Users, desc: 'Monitoruj ceny i listingi konkurencji' },
      { title: 'Monitoring', href: '/monitoring', icon: Activity, premiumOnly: true, desc: 'Sledz zmiany cen, pozycji i dostepnosci na marketplace' },
      { title: 'Wiadomosci', href: '/news', icon: Newspaper, desc: 'Aktualnosci i zmiany regulacji na marketplace' },
    ],
  },
]

// WHY: Compliance sub-tabs defined here so sidebar shows them as expandable menu
const complianceSubItems = [
  { key: 'dashboard', label: 'Panel Glowny', icon: BarChart3, desc: 'Przeglad zgodnosci i statusu regulacji' },
  { key: 'audit', label: 'Audyt', icon: Search, desc: 'Sprawdz zgodnosc produktow z regulacjami' },
  { key: 'settings', label: 'Aktywacja Alertow', icon: Bell, desc: 'Wlacz/wylacz powiadomienia o zmianach regulacji' },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle, desc: 'Lista alertow i zmian regulacji' },
  { key: 'integrations', label: 'Integracje', icon: Link2, desc: 'Polaczenia z marketplace i serwisami zewnetrznymi' },
  { key: 'upload', label: 'Upload', icon: Upload, desc: 'Wgraj dokumenty zgodnosci i certyfikaty' },
  { key: 'epr', label: 'Raporty EPR', icon: FileBarChart, desc: 'Raporty EPR wymagane przez regulacje UE' },
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
          Listing Builder Pro
        </h1>
        <p className="text-sm text-gray-400">System automatyzacji listingow</p>
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
                  <div key={item.href} className="group/nav relative">
                    <Link
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
                      {item.desc && (
                        <Info className={cn(
                          'h-3 w-3 ml-auto shrink-0 opacity-0 group-hover/nav:opacity-60 transition-opacity',
                          item.premiumOnly && tier !== 'premium' ? 'mr-0' : ''
                        )} />
                      )}
                    </Link>
                    {/* WHY: Tooltip shows on hover — positioned to the right of sidebar */}
                    {item.desc && (
                      <div className="pointer-events-none absolute left-full top-0 z-50 ml-2 hidden w-56 rounded-lg border border-gray-700 bg-[#1A1A1A] p-3 text-xs text-gray-300 shadow-xl group-hover/nav:block">
                        <p className="font-medium text-white mb-1">{item.title}</p>
                        {item.desc}
                      </div>
                    )}
                  </div>
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
              {complianceSubItems.map(({ key, label, icon: SubIcon, desc }) => {
                const isSubActive = isOnCompliance && activeComplianceTab === key
                return (
                  <div key={key} className="group/sub relative">
                    <Link
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
                    {desc && (
                      <div className="pointer-events-none absolute left-full top-0 z-50 ml-2 hidden w-52 rounded-lg border border-gray-700 bg-[#1A1A1A] p-3 text-xs text-gray-300 shadow-xl group-hover/sub:block">
                        <p className="font-medium text-white mb-1">{label}</p>
                        {desc}
                      </div>
                    )}
                  </div>
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
            Status API
          </p>
          <p className="text-xs font-mono text-green-500">
            {process.env.NODE_ENV === 'production' ? 'Produkcja' : 'Deweloperski'}
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
