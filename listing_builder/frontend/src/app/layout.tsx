// frontend/src/app/layout.tsx
// Purpose: Root layout with React Query provider and global navigation
// NOT for: Page-specific layouts or business logic

import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { AuthGuard } from '@/components/providers/AuthGuard'
import { AppShell } from '@/components/layout/AppShell'
import { MediaGenProvider } from '@/components/providers/MediaGenProvider'

export const metadata: Metadata = {
  title: 'OctoHelper — Asystent sprzedawcy',
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
      <body className="font-sans">
        <QueryProvider>
          <AuthProvider>
            <AuthGuard>
              <MediaGenProvider>
                <AppShell>
                  {children}
                </AppShell>
              </MediaGenProvider>
            </AuthGuard>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
