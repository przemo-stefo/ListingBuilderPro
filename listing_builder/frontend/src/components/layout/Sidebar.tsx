// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar — renders nav items from nav-config
// NOT for: Nav config data (that's nav-config.ts) or page content

'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname, useSearchParams } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useAdmin } from '@/lib/hooks/useAdmin'
import { TierBadge } from '@/components/tier/TierBadge'
import { navSections } from '@/components/layout/nav-config'
import { useMediaGen } from '@/components/providers/MediaGenProvider'
import { Newspaper, Info, Settings, UserCircle } from 'lucide-react'

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { tier, isLoading } = useTier()
  const { isAdmin } = useAdmin()
  const { activeJobs } = useMediaGen()

  // WHY: Close sidebar on mobile after navigating
  const handleNav = () => onClose?.()

  return (
    <div className="w-64 h-full border-r border-gray-800 bg-[#121212] p-6 flex flex-col">
      <div className="mb-6">
        <Image
          src="/logo-octohelper.png"
          alt="OctoHelper"
          width={180}
          height={29}
          className="mb-1"
          priority
        />
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
                const hrefQuery = item.href.split('?')[1] || ''
                // WHY: Items sharing a base path (e.g. /expert-qa?mode=strict vs ?mode=kaufland)
                // must match ALL query params from href, not just pathname
                const isActive = pathname === basePath && (
                  !hrefQuery || [...new URLSearchParams(hrefQuery)].every(([k, v]) => searchParams.get(k) === v)
                )
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
                          : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {item.title}
                      {/* WHY: Pulsing dot when background generation is running */}
                      {item.href === '/video-gen' && activeJobs.length > 0 && (
                        <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse shrink-0" title={`${activeJobs.length} generacji w toku`} />
                      )}
                      {item.beta && !isActive && (
                        <span className="rounded bg-amber-900/40 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                          BETA
                        </span>
                      )}
                      {item.desc && !item.beta && (
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

        {/* WHY: Wiadomości standalone — not part of nav-config (static link) */}
        <div>
          <div className="group/nav relative">
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
        <div className="flex items-center justify-center gap-1">
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
