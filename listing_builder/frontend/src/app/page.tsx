// frontend/src/app/page.tsx
// Purpose: Root redirect — unauthenticated → /login, authenticated → /dashboard
// NOT for: Landing page content (that's /pricing if needed)

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'

export default function RootRedirect() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return
    // WHY: Root page should never show content — redirect based on auth state
    if (user) {
      router.replace('/dashboard')
    } else {
      router.replace('/login')
    }
  }, [user, loading, router])

  return (
    <div className="flex h-screen items-center justify-center bg-[#1A1A1A]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-white" />
    </div>
  )
}
