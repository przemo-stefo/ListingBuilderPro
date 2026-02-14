// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar with links to all pages + tier badge
// NOT for: Page content or complex routing logic

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
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
} from 'lucide-react'

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
    title: 'Compliance',
    href: '/compliance',
    icon: Shield,
  },
  {
    title: 'Wiadomości',
    href: '/news',
    icon: Newspaper,
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
  const { tier } = useTier()

  return (
    <div className="w-64 border-r border-gray-800 bg-[#121212] p-6 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-white">
          Marketplace Listing
        </h1>
        <p className="text-sm text-gray-400">Automation System</p>
      </div>

      <nav className="space-y-2 flex-1">
        {navItems.map((item) => {
          // WHY: pathname-only match — query params ignored to avoid useSearchParams + Suspense
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
