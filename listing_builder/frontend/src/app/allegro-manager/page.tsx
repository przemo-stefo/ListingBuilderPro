// frontend/src/app/allegro-manager/page.tsx
// Purpose: Allegro Offers Manager — page orchestrator with OAuth check
// NOT for: Offer table logic (that's in components/OffersTable.tsx)

'use client'

import { useEffect, useState, useCallback } from 'react'
import { Store, Link2, Loader2 } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const ALLEGRO_FAQ = [
  { question: 'Jak polaczyc konto Allegro?', answer: 'Kliknij "Polacz z Allegro" — zostaniesz przekierowany na strone Allegro gdzie zaakceptujesz uprawnienia. Po powrocie system automatycznie pobierze Twoje oferty.' },
  { question: 'Co moge robic w Managerze Ofert?', answer: 'Mozesz przegladac swoje oferty Allegro, edytowac tytuly i ceny, oraz wlaczac/wylaczac oferty masowo. Zmiany sa synchronizowane bezposrednio z Allegro.' },
  { question: 'Czy polaczenie jest bezpieczne?', answer: 'Tak, uzywamy oficjalnego OAuth 2.0 Allegro. Twoje haslo nigdy nie jest przechowywane w naszym systemie — tylko token autoryzacyjny z ograniczonymi uprawnieniami.' },
]
import { FeatureGate } from '@/components/tier/FeatureGate'
import { getOAuthConnections, startAllegroOAuth } from '@/lib/api/converter'
import { useToast } from '@/lib/hooks/useToast'
import OffersTable from './components/OffersTable'

export default function AllegroManagerPage() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [connecting, setConnecting] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    getOAuthConnections()
      .then((conns) => {
        const allegro = conns.find((c) => c.marketplace === 'allegro')
        setConnected(allegro?.status === 'active')
      })
      .catch(() => {
        setConnected(false)
        toast({ title: 'Nie udało się sprawdzić połączenia z Allegro', variant: 'destructive' })
      })
  }, [toast])

  const handleConnect = useCallback(async () => {
    setConnecting(true)
    try {
      const { authorize_url } = await startAllegroOAuth()
      window.location.href = authorize_url
    } catch {
      setConnecting(false)
      toast({ title: 'Nie udało się rozpocząć autoryzacji Allegro', variant: 'destructive' })
    }
  }, [toast])

  return (
    <FeatureGate mode="redirect" redirectTo="/">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Store className="h-6 w-6" />
            Manager Ofert Allegro
          </h1>
          <p className="text-sm text-gray-400">
            Zarządzaj ofertami — edytuj tytuły, ceny, włączaj i wyłączaj masowo
          </p>
        </div>

        {connected === null && (
          <div className="flex items-center gap-2 py-8 justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
            <span className="text-sm text-gray-500">Sprawdzanie połączenia z Allegro...</span>
          </div>
        )}

        {connected === false && (
          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-8 text-center space-y-4">
            <Link2 className="h-10 w-10 text-gray-500 mx-auto" />
            <h2 className="text-lg font-semibold text-white">Połącz konto Allegro</h2>
            <p className="text-sm text-gray-400 max-w-md mx-auto">
              Aby zarządzać ofertami, musisz najpierw połączyć swoje konto Allegro przez OAuth.
            </p>
            <button
              onClick={handleConnect}
              disabled={connecting}
              className="rounded-lg bg-white px-6 py-2 text-sm font-medium text-black hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {connecting ? 'Łączenie...' : 'Połącz z Allegro'}
            </button>
          </div>
        )}

        {connected === true && <OffersTable />}

        <FaqSection
          title="Najczesciej zadawane pytania"
          subtitle="Allegro Manager"
          items={ALLEGRO_FAQ}
        />
      </div>
    </FeatureGate>
  )
}
