// frontend/src/app/compliance/components/AmazonConnectForm.tsx
// Purpose: Amazon SP-API credentials connect form (Client ID, Secret, Refresh Token)
// NOT for: Amazon OAuth redirect flow (that's handled by authorize/callback endpoints)

'use client'

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useToast } from '@/lib/hooks/useToast'
import { connectAmazon } from '@/lib/api/oauth'

interface AmazonConnectFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function AmazonConnectForm({ onSuccess, onCancel }: AmazonConnectFormProps) {
  const { toast } = useToast()
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [refreshToken, setRefreshToken] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleConnect() {
    if (!clientId.trim() || !clientSecret.trim() || !refreshToken.trim()) {
      toast({ title: 'Uzupełnij dane', description: 'Podaj Client ID, Client Secret i Refresh Token', variant: 'destructive' })
      return
    }
    setLoading(true)
    try {
      await connectAmazon(clientId.trim(), clientSecret.trim(), refreshToken.trim())
      toast({ title: 'Połączono!', description: 'Amazon SP-API podłączony pomyślnie' })
      onSuccess()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Nieprawidłowe dane'
      toast({ title: 'Błąd Amazon', description: msg, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-orange-500/30 bg-[#121212] p-5 space-y-4">
      <div>
        <h3 className="text-sm font-medium text-white">Połącz Amazon SP-API</h3>
        <p className="text-xs text-gray-400 mt-1">
          Wpisz dane z{' '}
          <a href="https://developer.amazonservices.com" target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:underline">
            Amazon Developer Central
          </a>
        </p>
      </div>
      <div className="space-y-3">
        <input
          type="text"
          placeholder="Client ID (amzn1.application-oa2-client.xxx)"
          value={clientId}
          onChange={e => setClientId(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-orange-500 focus:outline-none"
        />
        <input
          type="password"
          placeholder="Client Secret (amzn1.oa2-cs.v1.xxx)"
          value={clientSecret}
          onChange={e => setClientSecret(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-orange-500 focus:outline-none"
        />
        <input
          type="password"
          placeholder="Refresh Token (Atzr|xxx)"
          value={refreshToken}
          onChange={e => setRefreshToken(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-orange-500 focus:outline-none"
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleConnect}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg bg-orange-600 px-4 py-2 text-xs font-medium text-white hover:bg-orange-500 transition-colors disabled:opacity-50"
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
