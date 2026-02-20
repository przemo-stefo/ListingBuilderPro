// frontend/src/app/login/page.tsx
// Purpose: Login / registration / password reset — split layout with marketing copy
// NOT for: Dashboard or protected content

'use client'

import { Suspense, useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/components/providers/AuthProvider'
import { createClient } from '@/lib/supabase'
import { Mail, Lock, ArrowRight, ShieldCheck, Sparkles, BarChart3, Zap } from 'lucide-react'

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

// WHY: Rotating marketing slides — shows different value props
const slides = [
  {
    icon: Sparkles,
    headline: 'Zoptymalizuj swoje oferty',
    accent: 'z pomocą AI',
    desc: 'Tytuły, opisy, słowa kluczowe — wszystko generowane przez AI, dostosowane do algorytmów marketplace.',
  },
  {
    icon: BarChart3,
    headline: 'Analizuj konkurencję',
    accent: 'i bądź o krok przed nią',
    desc: 'Badanie rynku, ICP, brief reklamowy — 10 skilli AI do budowania przewagi konkurencyjnej.',
  },
  {
    icon: ShieldCheck,
    headline: 'Sprzedawaj na wielu',
    accent: 'marketplace jednocześnie',
    desc: 'Amazon, Allegro, eBay, Kaufland — konwertuj oferty między platformami jednym kliknięciem.',
  },
  {
    icon: Zap,
    headline: 'Ekspert AI odpowiada',
    accent: 'na Twoje pytania 24/7',
    desc: 'Baza wiedzy od top sprzedawców. Zadaj pytanie i otrzymaj konkretną odpowiedź opartą na danych.',
  },
]

function LoginContent() {
  const searchParams = useSearchParams()
  const isResetMode = searchParams.get('mode') === 'reset'

  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [activeSlide, setActiveSlide] = useState(0)
  const { user, loading, signIn, signUp, resetPassword } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user && !isResetMode) router.replace('/dashboard')
  }, [user, loading, router, isResetMode])

  // WHY: Auto-rotate slides every 5s
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide(prev => (prev + 1) % slides.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

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

  const handleSetNewPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSubmitting(true)

    try {
      if (newPassword.length < 6) {
        setError('Hasło musi mieć minimum 6 znaków')
        return
      }
      const supabase = createClient()
      const { error } = await supabase.auth.updateUser({ password: newPassword })
      if (error) {
        setError(error.message)
      } else {
        setMessage('Hasło zmienione! Przekierowuję...')
        setTimeout(() => router.push('/dashboard'), 1500)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const slide = slides[activeSlide]
  const SlideIcon = slide.icon

  // WHY: Shared left panel — marketing copy with rotating slides
  const leftPanel = (
    <div className="relative hidden lg:flex lg:w-1/2 flex-col justify-between p-12 overflow-hidden">
      {/* WHY: Subtle green radial glow — matches the screenshot aesthetic */}
      <div className="absolute inset-0 bg-[#0A0A0A]" />
      <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-emerald-500/8 blur-3xl" />
      <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-emerald-500/5 blur-3xl" />

      <div className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="h-5 w-5 text-emerald-400" />
          </div>
          <span className="text-lg font-semibold text-white">OctoHelper</span>
        </div>
      </div>

      <div className="relative z-10 space-y-6">
        <div className="flex items-center gap-3 mb-8">
          <SlideIcon className="h-8 w-8 text-emerald-400" />
        </div>
        <h2 className="text-4xl font-bold leading-tight text-white">
          {slide.headline}{' '}
          <span className="text-emerald-400">{slide.accent}</span>
        </h2>
        <p className="text-lg text-gray-400 max-w-md leading-relaxed">
          {slide.desc}
        </p>
      </div>

      <div className="relative z-10 flex items-center gap-3">
        <div className="flex gap-1.5">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setActiveSlide(i)}
              className={`h-2.5 w-2.5 rounded-full transition-all ${
                i === activeSlide
                  ? 'bg-emerald-400 w-6'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            />
          ))}
        </div>
        <span className="ml-4 text-sm text-gray-500">
          <span className="font-semibold text-white">500+</span> sprzedawców już korzysta
        </span>
      </div>
    </div>
  )

  // WHY: Reset mode — user clicked email link, session active, show new password form
  if (isResetMode) {
    return (
      <div className="flex min-h-screen bg-[#0A0A0A]">
        {leftPanel}
        <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            <div>
              <h1 className="text-2xl font-bold text-white">Ustaw nowe hasło</h1>
              <p className="mt-2 text-sm text-gray-400">Wpisz nowe hasło dla swojego konta</p>
            </div>

            <form onSubmit={handleSetNewPassword} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Nowe hasło</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    className="w-full rounded-xl border border-gray-800 bg-[#121212] pl-11 pr-4 py-3 text-sm text-white outline-none focus:border-emerald-500/50 transition-colors"
                    placeholder="Min. 6 znaków"
                    autoFocus
                  />
                </div>
              </div>

              {error && <ErrorMsg text={error} />}
              {message && <SuccessMsg text={message} />}

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 py-3 text-sm font-semibold text-white hover:bg-emerald-400 transition-colors disabled:opacity-50"
              >
                {submitting ? 'Zapisuję...' : 'Zmień hasło'}
                {!submitting && <ArrowRight className="h-4 w-4" />}
              </button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      {leftPanel}

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

            {error && <ErrorMsg text={error} />}
            {message && <SuccessMsg text={message} />}

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
                <button
                  onClick={handleReset}
                  className="block w-full text-gray-500 hover:text-gray-300 transition-colors"
                >
                  Zapomniałeś hasła?
                </button>
                <p>
                  Nie masz konta?{' '}
                  <button
                    onClick={() => { setTab('register'); setError(''); setMessage('') }}
                    className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Zarejestruj się
                  </button>
                </p>
              </div>
            ) : (
              <p>
                Masz już konto?{' '}
                <button
                  onClick={() => { setTab('login'); setError(''); setMessage('') }}
                  className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                >
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

function ErrorMsg({ text }: { text: string }) {
  return (
    <p className="rounded-xl border border-red-800 bg-red-900/20 px-4 py-2.5 text-sm text-red-400">
      {text}
    </p>
  )
}

function SuccessMsg({ text }: { text: string }) {
  return (
    <p className="rounded-xl border border-emerald-800 bg-emerald-900/20 px-4 py-2.5 text-sm text-emerald-400">
      {text}
    </p>
  )
}
