// frontend/src/components/layout/AppShell.tsx
// Purpose: Responsive layout — sidebar hidden on mobile, hamburger toggle
// NOT for: Auth logic (that's AuthProvider) or page content

'use client'

import { Suspense, useState, useEffect, type ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { TierProvider } from '@/components/providers/TierProvider'
import { Sidebar } from '@/components/layout/Sidebar'
import { Toaster } from '@/components/ui/toaster'
import { Menu, Bell, Settings, UserCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()

  // WHY: Auto-close mobile sidebar on route change (fixes "menu nie chowa się")
  useEffect(() => {
    setSidebarOpen(false)
  }, [pathname])

  // WHY: Login/register/landing pages get clean layout without sidebar
  if (loading || !user) {
    return <>{children}</>
  }

  return (
    <TierProvider>
      <div className="flex h-screen bg-[#1A1A1A]">
        {/* WHY: Dark overlay behind sidebar on mobile — click to close */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* WHY: w-64 shrink-0 on container guarantees stable width — prevents layout jump on desktop */}
        <div className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 md:static md:block md:shrink-0',
          sidebarOpen ? 'block' : 'hidden md:block'
        )}>
          <Suspense fallback={<div className="w-64 h-full bg-[#121212]" />}>
            <Sidebar onClose={() => setSidebarOpen(false)} />
          </Suspense>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* WHY: Header bar — hamburger on mobile, profile/settings/alerts icons on all screens */}
          <div className="flex items-center justify-between border-b border-gray-800 px-6 py-2.5">
            <div className="flex items-center gap-3 md:hidden">
              <button
                onClick={() => setSidebarOpen(true)}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <Menu className="h-5 w-5" />
              </button>
              <span className="text-sm font-bold text-white">OctoHelper</span>
            </div>
            <div className="hidden md:block" />
            <div className="flex items-center gap-1">
              <Link
                href="/compliance?tab=alerts"
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <Bell className="h-4 w-4" />
              </Link>
              <Link
                href="/settings"
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <Settings className="h-4 w-4" />
              </Link>
              <Link
                href="/account"
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <UserCircle className="h-4 w-4" />
              </Link>
            </div>
          </div>

          {/* WHY: overflow-y-scroll (not auto) prevents scrollbar appearing/disappearing = no layout jump */}
          <main className="flex-1 overflow-y-scroll p-4 md:p-8">
            {children}
          </main>
        </div>
      </div>
      <Toaster />
    </TierProvider>
  )
}
