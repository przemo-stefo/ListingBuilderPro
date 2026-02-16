// frontend/src/app/layout.tsx
// Purpose: Root layout with React Query provider and global navigation
// NOT for: Page-specific layouts or business logic

import type { Metadata } from 'next'
import { Suspense } from 'react'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { TierProvider } from '@/components/providers/TierProvider'
import { Sidebar } from '@/components/layout/Sidebar'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Octosello — Asystent sprzedawcy',
  description: 'AI-powered asystent sprzedawcy marketplace. Optymalizuj listingi, monitoruj compliance, konwertuj oferty.',
  icons: { icon: '/favicon.svg' },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pl" className="dark">
      <body className={inter.className}>
        <QueryProvider>
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
        </QueryProvider>
      </body>
    </html>
  )
}
