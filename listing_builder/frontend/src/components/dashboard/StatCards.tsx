// frontend/src/components/dashboard/StatCards.tsx
// Purpose: Dashboard stat cards grid — extracted for file size compliance
// NOT for: Data fetching (that's dashboard page)

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber } from '@/lib/utils'
import { Package, Sparkles, AlertCircle, TrendingUp, Clock } from 'lucide-react'
import type { DashboardStats } from '@/lib/types'

interface StatCardsProps {
  stats: DashboardStats
}

export function StatCards({ stats }: StatCardsProps) {
  const pendingCount = stats.pending_optimization || 0
  const optimizedCount = stats.optimized_products || 0

  const cards = [
    {
      title: 'Produkty', value: stats.total_products || 0, icon: Package,
      description: 'Wszystkie produkty w systemie', href: '/products',
    },
    {
      title: 'Do optymalizacji', value: pendingCount, icon: Clock,
      description: pendingCount > 0 ? 'Kliknij aby zoptymalizowac' : 'Brak czekajacych',
      color: pendingCount > 0 ? 'text-yellow-500' : 'text-gray-500',
      href: '/products?status=imported',
    },
    {
      title: 'Zoptymalizowane', value: optimizedCount, icon: Sparkles,
      description: optimizedCount > 0 ? 'Gotowe do eksportu' : 'Brak zoptymalizowanych',
      color: optimizedCount > 0 ? 'text-green-500' : 'text-gray-500',
      href: '/products?status=optimized',
    },
    {
      title: 'Sredni wynik', value: `${Math.round(stats.average_optimization_score || 0)}%`,
      icon: TrendingUp, description: 'Srednia ocena optymalizacji', color: 'text-green-500',
    },
    {
      title: 'Bledy', value: stats.failed_products || 0, icon: AlertCircle,
      description: 'Produkty z problemami', color: 'text-red-500', href: '/products?status=failed',
    },
    {
      title: 'Ostatni import', value: stats.recent_imports || 0, icon: Package,
      description: 'Ostatnie 24 godziny', href: '/products/import',
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {cards.map((stat) => {
        const Icon = stat.icon
        const inner = (
          <Card key={stat.title} className={stat.href ? 'hover:border-gray-600 transition-colors cursor-pointer' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">{stat.title}</CardTitle>
              <Icon className={`h-4 w-4 ${stat.color || 'text-gray-400'}`} />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${stat.color || 'text-white'}`}>
                {typeof stat.value === 'number' ? formatNumber(stat.value) : stat.value}
              </div>
              <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
            </CardContent>
          </Card>
        )
        return stat.href ? (
          <Link key={stat.title} href={stat.href}>{inner}</Link>
        ) : (
          <div key={stat.title}>{inner}</div>
        )
      })}
    </div>
  )
}
