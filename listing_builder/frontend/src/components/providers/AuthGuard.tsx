// frontend/src/components/providers/AuthGuard.tsx
// Purpose: Redirect unauthenticated users to /login
// NOT for: Auth state management (that's AuthProvider)

'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useEffect, type ReactNode } from 'react'
import { useAuth } from './AuthProvider'

// WHY: These pages don't require login
const PUBLIC_PATHS = ['/login', '/', '/privacy', '/terms']
const PUBLIC_PREFIXES = ['/payment/']

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true
  return PUBLIC_PREFIXES.some(prefix => pathname.startsWith(prefix))
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  useEffect(() => {
    if (loading) return
    if (!user && !isPublicPath(pathname)) {
      router.replace('/login')
    }
  }, [user, loading, pathname, router])

  // WHY: Show loading skeleton during session check — prevents content flash
  if (loading && !isPublicPath(pathname)) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#1A1A1A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-white" />
      </div>
    )
  }

  // WHY: Public pages always render (login, landing, etc.)
  if (isPublicPath(pathname)) {
    return <>{children}</>
  }

  // WHY: Don't render protected content until user is confirmed
  if (!user) return null

  return <>{children}</>
}
