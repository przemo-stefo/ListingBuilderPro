// frontend/src/components/layout/Sidebar.tsx
// Purpose: Main navigation sidebar with links to all pages
// NOT for: Page content or complex routing logic

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Package,
  ClipboardList,
  Hash,
  Users,
  Warehouse,
  BarChart3,
  Upload,
  Sparkles,
  Send,
  Settings
} from 'lucide-react'

const navItems = [
  {
    title: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    title: 'Products',
    href: '/products',
    icon: Package,
  },
  {
    title: 'Listings',
    href: '/listings',
    icon: ClipboardList,
  },
  {
    title: 'Keywords',
    href: '/keywords',
    icon: Hash,
  },
  {
    title: 'Competitors',
    href: '/competitors',
    icon: Users,
  },
  {
    title: 'Inventory',
    href: '/inventory',
    icon: Warehouse,
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
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
    title: 'Publish',
    href: '/publish',
    icon: Send,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 border-r border-gray-800 bg-[#121212] p-6">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-white">
          Marketplace Listing
        </h1>
        <p className="text-sm text-gray-400">Automation System</p>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
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
            </Link>
          )
        })}
      </nav>

      <div className="mt-auto pt-8">
        <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
          <p className="text-xs text-gray-400">
            Connected to backend
          </p>
          <p className="text-xs font-mono text-green-500">
            {process.env.NEXT_PUBLIC_API_URL || 'localhost:8000'}
          </p>
        </div>
      </div>
    </div>
  )
}
