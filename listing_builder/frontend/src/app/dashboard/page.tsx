// frontend/src/app/dashboard/page.tsx
// Purpose: Dashboard home page — orchestrator for stat cards, tiles, widgets
// NOT for: Product management or detailed views

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useDashboardStats } from '@/lib/hooks/useProducts'
import { apiClient } from '@/lib/api/client'
import { Package, Sparkles, ArrowRight, Link2, Upload } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'
import { FlowIndicator } from '@/components/ui/FlowIndicator'
import { WelcomeModal } from '@/components/ui/WelcomeModal'
import { OnboardingChecklist } from '@/components/ui/OnboardingChecklist'
import { ActivityFeed } from '@/components/ui/ActivityFeed'
import { StatCards } from '@/components/dashboard/StatCards'
import { AppTiles } from '@/components/dashboard/AppTiles'
import { ExpertWidget } from '@/components/dashboard/ExpertWidget'

const DASHBOARD_FAQ = [
  { question: 'Co pokazuje Pulpit?', answer: 'Pulpit wyświetla statystyki Twojego konta: liczbę produktów, status optymalizacji, średni wynik AI i ostatnie importy. To przegląd całego systemu w jednym miejscu.' },
  { question: 'Co oznacza "Do optymalizacji"?', answer: 'To produkty zaimportowane do systemu, które jeszcze nie zostały przetworzone przez AI. Kliknij "Optymalizuj listingi" aby je przetworzyć.' },
  { question: 'Jak działa Ekspert AI na Pulpicie?', answer: 'Widget Eksperta AI pozwala szybko zadać pytanie o sprzedaży na marketplace bez opuszczania Pulpitu. Wynik otwiera pełną stronę Eksperta AI z odpowiedzią opartego na wiedzy eksperckiej.' },
]

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats()
  const [expiredConnections, setExpiredConnections] = useState<string[]>([])
  // WHY: Derived from /oauth/status — reused by OnboardingChecklist (no extra API call)
  const [hasActiveOAuth, setHasActiveOAuth] = useState(false)

  // WHY: Check OAuth status on mount — show reconnect banner for expired connections
  // WHY: apiClient sends JWT (raw fetch() was missing it → 401 after require_user_id fix)
  useEffect(() => {
    apiClient.get('/oauth/status')
      .then(res => {
        const data = res.data
        if (!data?.connections) return
        const expired: string[] = []
        let hasActive = false
        // WHY: Single pass — derive both expired list and active flag
        for (const [key, val] of Object.entries(data.connections) as [string, any][]) {
          if (val.status === 'expired' || val.expires_soon) expired.push(key)
          if (val.status === 'active') hasActive = true
        }
        setExpiredConnections(expired)
        setHasActiveOAuth(hasActive)
      })
      .catch(() => {})
  }, [])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Pulpit</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2"><div className="h-4 w-24 bg-gray-700 rounded" /></CardHeader>
              <CardContent><div className="h-8 w-16 bg-gray-700 rounded" /></CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Pulpit</h1>
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-500">Błąd ładowania danych</CardTitle>
            <CardDescription>Nie udało się pobrać statystyk pulpitu</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const totalProducts = stats?.total_products || 0
  const pendingCount = stats?.pending_optimization || 0
  const optimizedCount = stats?.optimized_products || 0
  const publishedCount = stats?.published_products || 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Pulpit</h1>
        <p className="text-gray-400 mt-2">Przegląd Twojego panelu OctoHelper</p>
      </div>

      <FlowIndicator stats={stats ?? null} />

      {expiredConnections.length > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-800 bg-yellow-900/20 p-4">
          <Link2 className="h-5 w-5 shrink-0 text-yellow-500" />
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-400">
              {expiredConnections.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')} wymaga ponownego połączenia
            </p>
            <p className="text-xs text-yellow-600 mt-0.5">Token wygasł. Połącz ponownie w Integracje.</p>
          </div>
          <Link href="/integrations" className="rounded-lg bg-yellow-900/40 px-3 py-1.5 text-xs font-medium text-yellow-400 hover:bg-yellow-900/60 transition-colors">
            Połącz ponownie
          </Link>
        </div>
      )}

      <WelcomeModal totalProducts={totalProducts} />

      <OnboardingChecklist
        totalProducts={totalProducts}
        optimizedCount={optimizedCount}
        publishedCount={publishedCount}
        hasOAuth={hasActiveOAuth}
      />

      {totalProducts === 0 && (
        <div className="rounded-xl border border-dashed border-gray-700 bg-[#1A1A1A] p-12 text-center">
          <Package className="mx-auto h-12 w-12 text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Witaj w OctoHelper!</h2>
          <p className="text-gray-400 mb-6 max-w-md mx-auto">
            Zacznij od importu pierwszego produktu. Zaimportuj z Allegro, wklej URL lub dodaj dane ręcznie.
          </p>
          <div className="flex justify-center gap-3">
            <Link href="/products/import" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-medium text-black hover:bg-gray-200 transition-colors">
              <Upload className="h-4 w-4" />
              Importuj produkty
            </Link>
          </div>
        </div>
      )}

      {totalProducts > 0 && stats && <StatCards stats={stats} />}

      {pendingCount > 0 && (
        <Link
          href="/products?status=imported"
          className="flex items-center justify-between rounded-lg border border-yellow-800 bg-yellow-900/20 p-4 hover:bg-yellow-900/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            <div>
              <p className="text-sm font-medium text-yellow-400">
                Masz {pendingCount} {pendingCount === 1 ? 'produkt' : pendingCount < 5 ? 'produkty' : 'produktow'} do optymalizacji
              </p>
              <p className="text-xs text-yellow-600 mt-0.5">Kliknij aby przejsc do listy i zoptymalizowac listingi</p>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-yellow-500" />
        </Link>
      )}

      {stats && <AppTiles stats={stats} />}

      {totalProducts > 0 && <ActivityFeed />}

      <ExpertWidget />

      <FaqSection title="Najczęściej zadawane pytania" subtitle="Pulpit i nawigacja" items={DASHBOARD_FAQ} />
    </div>
  )
}
