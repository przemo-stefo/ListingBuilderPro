// frontend/src/components/layout/AppShell.tsx
// Purpose: Conditional sidebar layout — shows sidebar only for authenticated users
// NOT for: Auth logic (that's AuthProvider) or page content

'use client'

import { Suspense, type ReactNode } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { TierProvider } from '@/components/providers/TierProvider'
import { Sidebar } from '@/components/layout/Sidebar'
import { Toaster } from '@/components/ui/toaster'

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  // WHY: Login/register/landing pages get clean layout without sidebar
  if (loading || !user) {
    return <>{children}</>
  }

  return (
    <TierProvider>
      <div className="flex h-screen bg-[#1A1A1A]">
        <Suspense>
          <Sidebar />
        </Suspense>
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
      <Toaster />
    </TierProvider>
  )
}
