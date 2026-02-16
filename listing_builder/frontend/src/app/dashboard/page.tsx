// frontend/src/app/dashboard/page.tsx
// Purpose: Dashboard home page with stats and recent activity (moved from /)
// NOT for: Product management or detailed views

'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useDashboardStats } from '@/lib/hooks/useProducts'
import { formatNumber } from '@/lib/utils'
import { Package, Sparkles, Send, AlertCircle, TrendingUp, Clock } from 'lucide-react'

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats()

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
      title: 'Opublikowane',
      value: stats?.published_products || 0,
      icon: Send,
      description: 'Aktywne na marketplace',
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
      title: 'Sredni wynik',
      value: `${Math.round(stats?.average_optimization_score || 0)}%`,
      icon: TrendingUp,
      description: 'Srednia ocena optymalizacji',
      color: 'text-green-500',
    },
    {
      title: 'Ostatni import',
      value: stats?.recent_imports || 0,
      icon: Package,
      description: 'Ostatnie 24 godziny',
    },
    {
      title: 'Ostatnie publikacje',
      value: stats?.recent_publishes || 0,
      icon: Send,
      description: 'Ostatnie 24 godziny',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Pulpit</h1>
        <p className="text-gray-400 mt-2">
          Przeglad automatyzacji listingow na marketplace
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
          <a
            href="/publish"
            className="flex flex-col items-center justify-center p-6 rounded-lg border border-gray-700 hover:bg-gray-800 transition-colors"
          >
            <Send className="h-8 w-8 mb-2 text-green-500" />
            <span className="text-sm font-medium text-white">Publikuj na marketplace</span>
          </a>
        </CardContent>
      </Card>
    </div>
  )
}
