// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar — renders nav items + Compliance expandable
// NOT for: Nav config data (that's nav-config.ts) or page content

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useSearchParams, useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useAdmin } from '@/lib/hooks/useAdmin'
import { TierBadge } from '@/components/tier/TierBadge'
import { navSections, complianceSubItems } from '@/components/layout/nav-config'
import { Shield, ChevronDown, Newspaper, Info, Bell, Settings, UserCircle, Crown } from 'lucide-react'

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  const { tier, isPremium, isLoading } = useTier()
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
                // WHY: Premium items without license → show crown and redirect to upgrade
                const isLocked = item.premiumOnly && !isPremium

                return (
                  <div key={item.href} className="group/nav relative">
                    {isLocked ? (
                      <button
                        onClick={() => {
                          handleNav()
                          router.push('/account?upgrade=1')
                        }}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-800/50 transition-colors"
                      >
                        <Icon className="h-4 w-4" />
                        <span className="truncate">{item.title}</span>
                        {item.beta && (
                          <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                            BETA
                          </span>
                        )}
                        <Crown className="ml-auto h-3.5 w-3.5 text-amber-400 shrink-0" />
                      </button>
                    ) : (
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
                        {item.beta && !isActive && (
                          <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                            BETA
                          </span>
                        )}
                        {item.highlight && !isActive && !item.beta && (
                          <span className="ml-auto rounded bg-green-900/40 px-1.5 py-0.5 text-[10px] font-bold text-green-400">
                            AI
                          </span>
                        )}
                        {item.desc && !item.highlight && !item.beta && (
                          <Info className="h-3 w-3 ml-auto shrink-0 opacity-0 group-hover/nav:opacity-60 transition-opacity" />
                        )}
                      </Link>
                    )}
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

        {/* WHY: Compliance as expandable section — premium only, beta badge */}
        <div>
          <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
            Compliance
          </p>
          {/* WHY: Non-premium users see locked button redirecting to upgrade */}
          {!isPremium ? (
            <button
              onClick={() => {
                handleNav()
                router.push('/account?upgrade=1')
              }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-800/50 transition-colors"
            >
              <Shield className="h-4 w-4" />
              <span className="truncate">Compliance Guard</span>
              <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                BETA
              </span>
              <Crown className="ml-auto h-3.5 w-3.5 text-amber-400 shrink-0" />
            </button>
          ) : (
            <>
              <button
                onClick={() => setComplianceOpen(!complianceOpen)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors',
                  isOnCompliance ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                )}
              >
                <Shield className="h-4 w-4" />
                Compliance Guard
                {!isOnCompliance && (
                  <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                    BETA
                  </span>
                )}
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
            </>
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

      {/* Footer — quick links + tier badge + legal */}
      <div className="space-y-3 pt-4">
        {/* WHY: Bell/Settings/Account moved from top header bar to sidebar footer */}
        <div className="flex items-center justify-center gap-1">
          <Link
            href="/compliance?tab=alerts"
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            title="Alerty"
          >
            <Bell className="h-4 w-4" />
          </Link>
          <Link
            href="/settings"
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            title="Ustawienia"
          >
            <Settings className="h-4 w-4" />
          </Link>
          <Link
            href="/account"
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            title="Konto"
          >
            <UserCircle className="h-4 w-4" />
          </Link>
        </div>
        <div className="flex items-center justify-center">
          <TierBadge tier={tier} size="md" isLoading={isLoading} />
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
