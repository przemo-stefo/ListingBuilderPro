// frontend/src/app/login/page.tsx
// Purpose: Login / registration / password reset — form logic and routing
// NOT for: Marketing panel (LoginMarketingPanel) or reset form (ResetPasswordForm)

'use client'

import { Suspense, useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { LoginMarketingPanel } from '@/components/login/LoginMarketingPanel'
import { ResetPasswordForm } from '@/components/login/ResetPasswordForm'
import { Mail, Lock, ArrowRight, Sparkles } from 'lucide-react'

type Tab = 'login' | 'register'

// WHY: useSearchParams requires Suspense boundary in Next.js 14
export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-white" />
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}

function LoginContent() {
  const searchParams = useSearchParams()
  const isResetMode = searchParams.get('mode') === 'reset'

  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { user, loading, signIn, signUp, resetPassword } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user && !isResetMode) router.replace('/dashboard')
  }, [user, loading, router, isResetMode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSubmitting(true)

    try {
      if (tab === 'login') {
        const result = await signIn(email, password)
        if (result.error) setError(result.error)
        else router.push('/dashboard')
      } else {
        const result = await signUp(email, password)
        if (result.error) setError(result.error)
        else setMessage('Sprawdź email — wysłaliśmy link do potwierdzenia konta.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = async () => {
    if (!email) { setError('Wpisz email powyżej, a potem kliknij "Zapomniałeś hasła?"'); return }
    setError('')
    const result = await resetPassword(email)
    if (result.error) setError(result.error)
    else setMessage('Link do resetowania hasła wysłany na ' + email)
  }

  // WHY: Reset mode — user clicked email link, session active, show new password form
  if (isResetMode) {
    return (
      <div className="flex min-h-screen bg-[#0A0A0A]">
        <LoginMarketingPanel />
        <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
          <ResetPasswordForm />
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      <LoginMarketingPanel />
      <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* WHY: Mobile-only logo — desktop shows it in left panel */}
          <div className="lg:hidden flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="h-4 w-4 text-emerald-400" />
            </div>
            <span className="text-lg font-semibold text-white">OctoHelper</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold text-white">
              {tab === 'login' ? 'Zaloguj się' : 'Zarejestruj się'}
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              {tab === 'login'
                ? 'Wpisz swoje dane, aby uzyskać dostęp do panelu'
                : 'Utwórz konto, aby zacząć optymalizować oferty'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Adres email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-gray-800 bg-[#121212] pl-11 pr-4 py-3 text-sm text-white outline-none focus:border-emerald-500/50 transition-colors"
                  placeholder="jan@firma.pl"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Hasło</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-gray-800 bg-[#121212] pl-11 pr-4 py-3 text-sm text-white outline-none focus:border-emerald-500/50 transition-colors"
                  placeholder="Min. 6 znaków"
                />
              </div>
            </div>

            {error && <p className="rounded-xl border border-red-800 bg-red-900/20 px-4 py-2.5 text-sm text-red-400">{error}</p>}
            {message && <p className="rounded-xl border border-emerald-800 bg-emerald-900/20 px-4 py-2.5 text-sm text-emerald-400">{message}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 py-3 text-sm font-semibold text-white hover:bg-emerald-400 transition-colors disabled:opacity-50"
            >
              {submitting ? 'Ładowanie...' : tab === 'login' ? 'Zaloguj się' : 'Zarejestruj się'}
              {!submitting && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>

          <div className="text-center text-sm text-gray-500">
            {tab === 'login' ? (
              <div className="space-y-3">
                <button onClick={handleReset} className="block w-full text-gray-500 hover:text-gray-300 transition-colors">
                  Zapomniałeś hasła?
                </button>
                <p>
                  Nie masz konta?{' '}
                  <button onClick={() => { setTab('register'); setError(''); setMessage('') }} className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
                    Zarejestruj się
                  </button>
                </p>
              </div>
            ) : (
              <p>
                Masz już konto?{' '}
                <button onClick={() => { setTab('login'); setError(''); setMessage('') }} className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
                  Zaloguj się
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
