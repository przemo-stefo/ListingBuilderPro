// frontend/src/app/compliance/components/RozetkaConnectForm.tsx
// Purpose: Rozetka seller credentials connect form (login + password)
// NOT for: Other marketplace OAuth flows (those use browser redirect)

'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useToast } from '@/lib/hooks/useToast'
import { connectRozetka } from '@/lib/api/oauth'

interface RozetkaConnectFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function RozetkaConnectForm({ onSuccess, onCancel }: RozetkaConnectFormProps) {
  const { toast } = useToast()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleConnect() {
    if (!username.trim() || !password.trim()) {
      toast({ title: 'Uzupełnij dane', description: 'Podaj login i hasło sprzedawcy Rozetka', variant: 'destructive' })
      return
    }
    setLoading(true)
    try {
      await connectRozetka(username.trim(), password.trim())
      toast({ title: 'Połączono!', description: 'Rozetka podłączona pomyślnie' })
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Nieprawidłowe dane'
      toast({ title: 'Błąd Rozetka', description: msg, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-yellow-500/30 bg-[#121212] p-5 space-y-4">
      <div>
        <h3 className="text-sm font-medium text-white">Połącz Rozetka</h3>
        <p className="text-xs text-gray-400 mt-1">
          Wpisz login i hasło konta sprzedawcy Rozetka (Seller Portal)
        </p>
      </div>
      <div className="space-y-3">
        <input
          type="text"
          placeholder="Login (email)"
          value={username}
          onChange={e => setUsername(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-yellow-500 focus:outline-none"
        />
        <input
          type="password"
          placeholder="Hasło"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-yellow-500 focus:outline-none"
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleConnect}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg bg-yellow-600 px-4 py-2 text-xs font-medium text-white hover:bg-yellow-500 transition-colors disabled:opacity-50"
        >
          {loading && <Loader2 className="h-3 w-3 animate-spin" />}
          {loading ? 'Łączenie...' : 'Połącz'}
        </button>
        <button
          onClick={onCancel}
          className="rounded-lg px-4 py-2 text-xs text-gray-400 hover:text-white transition-colors"
        >
          Anuluj
        </button>
      </div>
    </div>
  )
}
