// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar — renders nav items + Compliance expandable
// NOT for: Nav config data (that's nav-config.ts) or page content

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useAdmin } from '@/lib/hooks/useAdmin'
import { TierBadge } from '@/components/tier/TierBadge'
import { navSections, complianceSubItems } from '@/components/layout/nav-config'
import { Shield, ChevronDown, Newspaper, Info } from 'lucide-react'

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { tier, isLoading } = useTier()
  const { isAdmin } = useAdmin()

  // WHY: Auto-expand when user is on /compliance, collapse otherwise
  const isOnCompliance = pathname === '/compliance'
  const [complianceOpen, setComplianceOpen] = useState(isOnCompliance)
  const activeComplianceTab = searchParams.get('tab') || 'dashboard'

  // WHY: Close sidebar on mobile after navigating
  const handleNav = () => onClose?.()

  return (
    <div className="w-64 h-full border-r border-gray-800 bg-[#121212] p-6 flex flex-col">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">OctoHelper</h1>
        <p className="text-sm text-gray-400">Asystent sprzedawcy marketplace</p>
      </div>

      <nav className="flex-1 overflow-y-auto space-y-4">
        {/* WHY: Filter out Admin section for non-admin users */}
        {navSections.filter(s => s.label !== 'Admin' || isAdmin).map((section) => (
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
                      onClick={handleNav}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
                        isActive
                          ? 'bg-white text-black'
                          : item.highlight
                            ? 'text-green-400 hover:bg-green-900/20 hover:text-green-300'
                            : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.title}
                      {item.highlight && !isActive && (
                        <span className="ml-auto rounded bg-green-900/40 px-1.5 py-0.5 text-[10px] font-bold text-green-400">
                          AI
                        </span>
                      )}
                      {item.desc && !item.highlight && (
                        <Info className="h-3 w-3 ml-auto shrink-0 opacity-0 group-hover/nav:opacity-60 transition-opacity" />
                      )}
                    </Link>
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
              isOnCompliance ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            )}
          >
            <Shield className="h-4 w-4" />
            Compliance Guard
            <ChevronDown className={cn('ml-auto h-4 w-4 transition-transform', complianceOpen && 'rotate-180')} />
          </button>

          {complianceOpen && (
            <div className="ml-3 mt-1 space-y-0.5 border-l border-gray-800 pl-3">
              {complianceSubItems.map(({ key, label, icon: SubIcon, desc }) => {
                const isSubActive = isOnCompliance && activeComplianceTab === key
                return (
                  <div key={key} className="group/sub relative">
                    <Link
                      href={`/compliance?tab=${key}`}
                      onClick={handleNav}
                      className={cn(
                        'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-xs transition-colors',
                        isSubActive ? 'bg-white/10 text-white' : 'text-gray-500 hover:bg-gray-800/50 hover:text-gray-300'
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

          <div className="group/nav relative mt-0.5">
            <Link
              href="/news"
              onClick={handleNav}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
                pathname === '/news' ? 'bg-white text-black' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Newspaper className="h-4 w-4" />
              Wiadomości
            </Link>
          </div>
        </div>
      </nav>

      {/* Footer — tier badge + legal links */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-center">
          <TierBadge tier={tier} size="md" isLoading={isLoading} />
        </div>
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
          <p className="text-xs text-gray-400">Status API</p>
          <p className="text-xs font-mono text-green-500">
            {process.env.NODE_ENV === 'production' ? 'Produkcja' : 'Deweloperski'}
          </p>
        </div>
        <div className="flex justify-center gap-3 text-[10px] text-gray-600">
          <Link href="/privacy" className="hover:text-gray-400 transition-colors">Prywatność</Link>
          <span>·</span>
          <Link href="/terms" className="hover:text-gray-400 transition-colors">Regulamin</Link>
        </div>
      </div>
    </div>
  )
}
