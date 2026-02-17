// frontend/src/app/dashboard/page.tsx
// Purpose: Dashboard home page with stats, quick actions, and Expert AI widget
// NOT for: Product management or detailed views

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useDashboardStats } from '@/lib/hooks/useProducts'
import { formatNumber } from '@/lib/utils'
import { Package, Sparkles, AlertCircle, TrendingUp, Clock, Brain, Send, ArrowRight } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const DASHBOARD_FAQ = [
  { question: 'Co pokazuje Pulpit?', answer: 'Pulpit wyswietla statystyki Twojego konta: liczbe produktow, status optymalizacji, sredni wynik AI i ostatnie importy. To przeglad calego systemu w jednym miejscu.' },
  { question: 'Co oznacza "Do optymalizacji"?', answer: 'To produkty zaimportowane do systemu, ktore jeszcze nie zostaly przetworzone przez AI. Kliknij "Optymalizuj listingi" aby je przetworzyc.' },
  { question: 'Jak dziala Ekspert AI na Pulpicie?', answer: 'Widget Eksperta AI pozwala szybko zadac pytanie o sprzedazy na marketplace bez opuszczania Pulpitu. Wynik otwiera pelna strone Eksperta AI z odpowiedzia opartego na wiedzy eksperckiej.' },
]

const SUGGESTED_QUESTIONS = [
  'Jak znalezc najlepsze slowa kluczowe?',
  'Jak zoptymalizowac tytul na Amazon DE?',
  'Jak dziala algorytm A9/COSMO?',
]

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats()
  const router = useRouter()
  const [expertQuestion, setExpertQuestion] = useState('')

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
            <CardTitle className="text-red-500">Blad ladowania danych</CardTitle>
            <CardDescription>Nie udalo sie pobrac statystyk pulpitu</CardDescription>
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
      description: 'Czekajace na optymalizacje AI',
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
      title: 'Sredni wynik',
      value: `${Math.round(stats?.average_optimization_score || 0)}%`,
      icon: TrendingUp,
      description: 'Srednia ocena optymalizacji',
      color: 'text-green-500',
    },
    {
      title: 'Bledy',
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
          Przeglad Twojego panelu Octosello
        </p>
      </div>

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

      <Card>
        <CardHeader>
          <CardTitle>Szybkie akcje</CardTitle>
          <CardDescription>
            Najczesciej uzywane funkcje
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <a
            href="/products/import"
            className="flex flex-col items-center justify-center p-6 rounded-lg border border-gray-700 hover:bg-gray-800 transition-colors"
          >
            <Package className="h-8 w-8 mb-2 text-white" />
            <span className="text-sm font-medium text-white">Importuj produkty</span>
          </a>
          <a
            href="/optimize"
            className="flex flex-col items-center justify-center p-6 rounded-lg border border-gray-700 hover:bg-gray-800 transition-colors"
          >
            <Sparkles className="h-8 w-8 mb-2 text-blue-500" />
            <span className="text-sm font-medium text-white">Optymalizuj listingi</span>
          </a>
          {/* WHY: Replaced "Publikuj na marketplace" with "Ekspert AI" — Publish hidden in MVP */}
          <a
            href="/expert-qa"
            className="flex flex-col items-center justify-center p-6 rounded-lg border border-green-900/30 hover:bg-green-900/10 transition-colors"
          >
            <Brain className="h-8 w-8 mb-2 text-green-400" />
            <span className="text-sm font-medium text-green-400">Ekspert AI</span>
          </a>
        </CardContent>
      </Card>

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
              placeholder="Np. Jak zoptymalizowac backend keywords?"
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
        title="Najczesciej zadawane pytania"
        subtitle="Pulpit i nawigacja"
        items={DASHBOARD_FAQ}
      />
    </div>
  )
}
