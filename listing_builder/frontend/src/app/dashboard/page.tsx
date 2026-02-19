// frontend/src/app/dashboard/page.tsx
// Purpose: Dashboard home page with stats, app tiles, and Expert AI widget
// NOT for: Product management or detailed views

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useDashboardStats } from '@/lib/hooks/useProducts'
import { formatNumber } from '@/lib/utils'
import { Package, Sparkles, AlertCircle, TrendingUp, Clock, Brain, Send, ArrowRight, Link2, Upload, Database, ArrowRightLeft } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const DASHBOARD_FAQ = [
  { question: 'Co pokazuje Pulpit?', answer: 'Pulpit wyświetla statystyki Twojego konta: liczbę produktów, status optymalizacji, średni wynik AI i ostatnie importy. To przegląd całego systemu w jednym miejscu.' },
  { question: 'Co oznacza "Do optymalizacji"?', answer: 'To produkty zaimportowane do systemu, które jeszcze nie zostały przetworzone przez AI. Kliknij "Optymalizuj listingi" aby je przetworzyć.' },
  { question: 'Jak działa Ekspert AI na Pulpicie?', answer: 'Widget Eksperta AI pozwala szybko zadać pytanie o sprzedaży na marketplace bez opuszczania Pulpitu. Wynik otwiera pełną stronę Eksperta AI z odpowiedzią opartego na wiedzy eksperckiej.' },
]

const SUGGESTED_QUESTIONS = [
  'Jak znaleźć najlepsze słowa kluczowe?',
  'Jak zoptymalizować tytuł na Amazon DE?',
  'Jak działa algorytm A9/COSMO?',
]

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats()
  const router = useRouter()
  const [expertQuestion, setExpertQuestion] = useState('')
  const [expiredConnections, setExpiredConnections] = useState<string[]>([])

  // WHY: Check OAuth status on mount — show reconnect banner for expired connections
  useEffect(() => {
    fetch('/api/proxy/oauth/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data?.connections) return
        const expired = Object.entries(data.connections)
          .filter(([_, v]: [string, any]) => v.status === 'expired')
          .map(([k]) => k)
        setExpiredConnections(expired)
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
              <CardHeader className="pb-2">
                <div className="h-4 w-24 bg-gray-700 rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-gray-700 rounded" />
              </CardContent>
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

  // WHY: Removed "Opublikowane" and "Ostatnie publikacje" — Publish page hidden in MVP
  const statCards = [
    {
      title: 'Produkty',
      value: stats?.total_products || 0,
      icon: Package,
      description: 'Wszystkie produkty w systemie',
    },
    {
      title: 'Do optymalizacji',
      value: stats?.pending_optimization || 0,
      icon: Clock,
      description: 'Czekające na optymalizację AI',
      color: 'text-yellow-500',
    },
    {
      title: 'Zoptymalizowane',
      value: stats?.optimized_products || 0,
      icon: Sparkles,
      description: 'Przetworzone przez AI',
      color: 'text-blue-500',
    },
    {
      title: 'Średni wynik',
      value: `${Math.round(stats?.average_optimization_score || 0)}%`,
      icon: TrendingUp,
      description: 'Średnia ocena optymalizacji',
      color: 'text-green-500',
    },
    {
      title: 'Błędy',
      value: stats?.failed_products || 0,
      icon: AlertCircle,
      description: 'Produkty z problemami',
      color: 'text-red-500',
    },
    {
      title: 'Ostatni import',
      value: stats?.recent_imports || 0,
      icon: Package,
      description: 'Ostatnie 24 godziny',
    },
  ]

  const handleExpertSubmit = () => {
    if (!expertQuestion.trim()) return
    router.push(`/expert-qa?q=${encodeURIComponent(expertQuestion.trim())}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Pulpit</h1>
        <p className="text-gray-400 mt-2">
          Przegląd Twojego panelu OctoHelper
        </p>
      </div>

      {expiredConnections.length > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-800 bg-yellow-900/20 p-4">
          <Link2 className="h-5 w-5 shrink-0 text-yellow-500" />
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-400">
              {expiredConnections.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')} wymaga ponownego połączenia
            </p>
            <p className="text-xs text-yellow-600 mt-0.5">Token wygasł. Połącz ponownie w Integracje.</p>
          </div>
          <Link
            href="/integrations"
            className="rounded-lg bg-yellow-900/40 px-3 py-1.5 text-xs font-medium text-yellow-400 hover:bg-yellow-900/60 transition-colors"
          >
            Połącz ponownie
          </Link>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color || 'text-gray-400'}`} />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${stat.color || 'text-white'}`}>
                  {typeof stat.value === 'number' ? formatNumber(stat.value) : stat.value}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* WHY: 4 app tiles — each links to a core workflow (Import, Products, Converter, Optimizer) */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link
          href="/products/import"
          className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors"
        >
          <Upload className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
          <h3 className="text-sm font-semibold text-white mb-1">Importer</h3>
          <p className="text-xs text-gray-500">CSV, Allegro URL lub ręcznie</p>
          {(stats?.recent_imports ?? 0) > 0 && (
            <p className="text-xs text-gray-400 mt-2">{stats?.recent_imports} importów (24h)</p>
          )}
        </Link>
        <Link
          href="/products"
          className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors"
        >
          <Database className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
          <h3 className="text-sm font-semibold text-white mb-1">Baza Produktów</h3>
          <p className="text-xs text-gray-500">Przeglądaj i zarządzaj produktami</p>
          <p className="text-xs text-gray-400 mt-2">{formatNumber(stats?.total_products || 0)} produktów</p>
        </Link>
        <Link
          href="/converter"
          className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors"
        >
          <ArrowRightLeft className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
          <h3 className="text-sm font-semibold text-white mb-1">Konwerter</h3>
          <p className="text-xs text-gray-500">Allegro → Amazon/eBay/Kaufland</p>
        </Link>
        <Link
          href="/optimize"
          className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors"
        >
          <Sparkles className="h-8 w-8 mb-3 text-blue-500 group-hover:text-blue-400 transition-colors" />
          <h3 className="text-sm font-semibold text-white mb-1">Optymalizator</h3>
          <p className="text-xs text-gray-500">AI generuje tytuł, bullety, opis</p>
          {(stats?.average_optimization_score ?? 0) > 0 && (
            <p className="text-xs text-green-500 mt-2">Średnia: {Math.round(stats?.average_optimization_score || 0)}%</p>
          )}
        </Link>
      </div>

      {/* WHY: Expert AI widget on dashboard — makes the feature more discoverable */}
      <Card className="border-green-900/30">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-green-400" />
            <CardTitle className="text-green-400">Zapytaj Eksperta AI</CardTitle>
          </div>
          <CardDescription>
            Odpowiedzi na bazie wiedzy eksperckiej o Amazon, e-commerce i PPC
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={expertQuestion}
              onChange={e => setExpertQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleExpertSubmit()}
              placeholder="Np. Jak zoptymalizować backend keywords?"
              className="flex-1 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-green-800"
            />
            <button
              onClick={handleExpertSubmit}
              disabled={!expertQuestion.trim()}
              className="rounded-lg bg-green-900/40 px-4 py-2.5 text-green-400 hover:bg-green-900/60 transition-colors disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => router.push(`/expert-qa?q=${encodeURIComponent(q)}`)}
                className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-1.5 text-xs text-gray-400 hover:border-green-800 hover:text-green-400 transition-colors"
              >
                {q}
                <ArrowRight className="inline ml-1 h-3 w-3" />
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <FaqSection
        title="Najczęściej zadawane pytania"
        subtitle="Pulpit i nawigacja"
        items={DASHBOARD_FAQ}
      />
    </div>
  )
}
