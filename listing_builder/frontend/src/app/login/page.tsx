// frontend/src/app/login/page.tsx
// Purpose: Login / registration page with Supabase Auth
// NOT for: Dashboard or protected content

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'

type Tab = 'login' | 'register'

export default function LoginPage() {
  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { user, loading, signIn, signUp, resetPassword } = useAuth()
  const router = useRouter()

  // WHY: Logged-in user visiting /login should go straight to dashboard
  useEffect(() => {
    if (!loading && user) router.replace('/dashboard')
  }, [user, loading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSubmitting(true)

    try {
      if (tab === 'login') {
        const result = await signIn(email, password)
        if (result.error) {
          setError(result.error)
        } else {
          router.push('/dashboard')
        }
      } else {
        const result = await signUp(email, password)
        if (result.error) {
          setError(result.error)
        } else {
          setMessage('Sprawdź email — wysłaliśmy link do potwierdzenia konta.')
        }
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = async () => {
    if (!email) {
      setError('Wpisz email powyżej, a potem kliknij "Zapomniałeś hasła?"')
      return
    }
    setError('')
    const result = await resetPassword(email)
    if (result.error) {
      setError(result.error)
    } else {
      setMessage('Link do resetowania hasła wysłany na ' + email)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#1A1A1A]">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">OctoHelper</h1>
          <p className="mt-1 text-sm text-gray-400">Asystent sprzedawcy marketplace</p>
        </div>

        {/* WHY: Tabs — login/register share the same form, just different action */}
        <div className="flex rounded-lg border border-gray-800 bg-[#121212] p-1">
          <button
            onClick={() => { setTab('login'); setError(''); setMessage('') }}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${
              tab === 'login' ? 'bg-white text-black' : 'text-gray-400 hover:text-white'
            }`}
          >
            Zaloguj się
          </button>
          <button
            onClick={() => { setTab('register'); setError(''); setMessage('') }}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${
              tab === 'register' ? 'bg-white text-black' : 'text-gray-400 hover:text-white'
            }`}
          >
            Zarejestruj się
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-[#121212] px-4 py-2.5 text-sm text-white outline-none focus:border-gray-600"
              placeholder="twoj@email.com"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Hasło</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-800 bg-[#121212] px-4 py-2.5 text-sm text-white outline-none focus:border-gray-600"
              placeholder="Min. 6 znaków"
            />
          </div>

          {error && (
            <p className="rounded-lg border border-red-800 bg-red-900/20 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          {message && (
            <p className="rounded-lg border border-green-800 bg-green-900/20 px-3 py-2 text-sm text-green-400">
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-white py-2.5 text-sm font-medium text-black hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            {submitting ? 'Ładowanie...' : tab === 'login' ? 'Zaloguj się' : 'Zarejestruj się'}
          </button>
        </form>

        {tab === 'login' && (
          <button
            onClick={handleReset}
            className="block w-full text-center text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Zapomniałeś hasła?
          </button>
        )}
      </div>
    </div>
  )
}
