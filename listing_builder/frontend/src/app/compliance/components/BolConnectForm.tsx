// frontend/src/app/compliance/components/BolConnectForm.tsx
// Purpose: BOL.com Client Credentials connect form
// NOT for: Other marketplace OAuth flows (those use browser redirect)

'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useToast } from '@/lib/hooks/useToast'
import { connectBol } from '@/lib/api/oauth'

interface BolConnectFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function BolConnectForm({ onSuccess, onCancel }: BolConnectFormProps) {
  const { toast } = useToast()
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleConnect() {
    if (!clientId.trim() || !clientSecret.trim()) {
      toast({ title: 'Uzupełnij dane', description: 'Podaj Client ID i Client Secret', variant: 'destructive' })
      return
    }
    setLoading(true)
    try {
      await connectBol(clientId.trim(), clientSecret.trim())
      toast({ title: 'Połączono!', description: 'BOL.com podłączony pomyślnie' })
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Nieprawidłowe dane'
      toast({ title: 'Błąd BOL.com', description: msg, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-blue-500/30 bg-[#121212] p-5 space-y-4">
      <div>
        <h3 className="text-sm font-medium text-white">Połącz BOL.com</h3>
        <p className="text-xs text-gray-400 mt-1">
          Wpisz Client ID i Client Secret z BOL Partner Platform
        </p>
      </div>
      <div className="space-y-3">
        <input
          type="text"
          placeholder="Client ID"
          value={clientId}
          onChange={e => setClientId(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
        <input
          type="password"
          placeholder="Client Secret"
          value={clientSecret}
          onChange={e => setClientSecret(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleConnect}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-500 transition-colors disabled:opacity-50"
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
