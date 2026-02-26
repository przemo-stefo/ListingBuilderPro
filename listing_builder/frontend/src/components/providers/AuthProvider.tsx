// frontend/src/components/providers/AuthProvider.tsx
// Purpose: Supabase Auth context — user session, login/logout state
// NOT for: Tier/premium logic (that's TierProvider) or API calls

'use client'

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { createClient } from '@/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error?: string }>
  signUp: (email: string, password: string) => Promise<{ error?: string }>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<{ error?: string }>
}

const AuthCtx = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signIn: async () => ({}),
  signUp: async () => ({}),
  signOut: async () => {},
  resetPassword: async () => ({}),
})

export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()

    // WHY: Get initial session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // WHY: Listen for auth changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) return { error: error.message }
    return {}
  }, [])

  const signUp = useCallback(async (email: string, password: string) => {
    const supabase = createClient()
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) return { error: error.message }
    return {}
  }, [])

  const signOut = useCallback(async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    // WHY: Clear license key + owner on logout — prevents next user inheriting premium
    // localStorage is per-domain, not per-user. Without this, logging into
    // a different account would inherit the previous user's premium status.
    localStorage.removeItem('lbp_license_key')
    localStorage.removeItem('lbp_license_owner')
    setUser(null)
    setSession(null)
  }, [])

  const resetPassword = useCallback(async (email: string) => {
    const supabase = createClient()
    // WHY: redirectTo → /auth/callback exchanges PKCE code, then redirects to /login?mode=reset
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent('/login?mode=reset')}`,
    })
    if (error) return { error: error.message }
    return {}
  }, [])

  return (
    <AuthCtx.Provider value={{ user, session, loading, signIn, signUp, signOut, resetPassword }}>
      {children}
    </AuthCtx.Provider>
  )
}
