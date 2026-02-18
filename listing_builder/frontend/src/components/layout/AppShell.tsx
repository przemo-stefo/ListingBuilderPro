// frontend/src/components/layout/AppShell.tsx
// Purpose: Responsive layout — sidebar hidden on mobile, hamburger toggle
// NOT for: Auth logic (that's AuthProvider) or page content

'use client'

import { Suspense, useState, type ReactNode } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { TierProvider } from '@/components/providers/TierProvider'
import { Sidebar } from '@/components/layout/Sidebar'
import { Toaster } from '@/components/ui/toaster'
import { Menu } from 'lucide-react'
import { cn } from '@/lib/utils'

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

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

        {/* Sidebar — always visible on md+, slide-in overlay on mobile */}
        <div className={cn(
          'fixed inset-y-0 left-0 z-50 md:static md:block',
          sidebarOpen ? 'block' : 'hidden md:block'
        )}>
          <Suspense>
            <Sidebar onClose={() => setSidebarOpen(false)} />
          </Suspense>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* WHY: Mobile-only header bar with hamburger — desktop has sidebar always visible */}
          <div className="flex items-center gap-3 border-b border-gray-800 px-4 py-3 md:hidden">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-sm font-bold text-white">OctoHelper</span>
          </div>

          <main className="flex-1 overflow-y-auto p-4 md:p-8">
            {children}
          </main>
        </div>
      </div>
      <Toaster />
    </TierProvider>
  )
}
