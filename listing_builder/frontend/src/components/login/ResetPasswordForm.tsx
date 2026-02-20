// frontend/src/components/login/ResetPasswordForm.tsx
// Purpose: New password form — shown after user clicks password reset email link
// NOT for: Login/register forms (that's login/page.tsx)

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { Lock, ArrowRight } from 'lucide-react'

export function ResetPasswordForm() {
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
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

  return (
    <div className="w-full max-w-md space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Ustaw nowe hasło</h1>
        <p className="mt-2 text-sm text-gray-400">Wpisz nowe hasło dla swojego konta</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
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

        {error && <p className="rounded-xl border border-red-800 bg-red-900/20 px-4 py-2.5 text-sm text-red-400">{error}</p>}
        {message && <p className="rounded-xl border border-emerald-800 bg-emerald-900/20 px-4 py-2.5 text-sm text-emerald-400">{message}</p>}

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
  )
}
