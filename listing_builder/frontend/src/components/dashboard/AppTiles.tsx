// frontend/src/components/dashboard/AppTiles.tsx
// Purpose: Dashboard 4 app tiles grid — extracted for file size compliance
// NOT for: Data fetching

import Link from 'next/link'
import { Upload, Database, ArrowRightLeft, Sparkles } from 'lucide-react'
import { formatNumber } from '@/lib/utils'
import type { DashboardStats } from '@/lib/types'

interface AppTilesProps {
  stats: DashboardStats
}

export function AppTiles({ stats }: AppTilesProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Link href="/products/import" className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors">
        <Upload className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
        <h3 className="text-sm font-semibold text-white mb-1">Importer</h3>
        <p className="text-xs text-gray-500">CSV, Allegro URL lub ręcznie</p>
        {(stats.recent_imports ?? 0) > 0 && (
          <p className="text-xs text-gray-400 mt-2">{stats.recent_imports} importów (24h)</p>
        )}
      </Link>
      <Link href="/products" className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors">
        <Database className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
        <h3 className="text-sm font-semibold text-white mb-1">Baza Produktów</h3>
        <p className="text-xs text-gray-500">Przeglądaj i zarządzaj produktami</p>
        <p className="text-xs text-gray-400 mt-2">{formatNumber(stats.total_products || 0)} produktów</p>
      </Link>
      <Link href="/converter" className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors">
        <ArrowRightLeft className="h-8 w-8 mb-3 text-gray-400 group-hover:text-white transition-colors" />
        <h3 className="text-sm font-semibold text-white mb-1">Konwerter</h3>
        <p className="text-xs text-gray-500">Allegro → Amazon/eBay/Kaufland</p>
      </Link>
      <Link href="/optimize" className="group rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 hover:border-gray-600 transition-colors">
        <Sparkles className="h-8 w-8 mb-3 text-blue-500 group-hover:text-blue-400 transition-colors" />
        <h3 className="text-sm font-semibold text-white mb-1">Optymalizator</h3>
        <p className="text-xs text-gray-500">AI generuje tytuł, bullety, opis</p>
        {(stats.average_optimization_score ?? 0) > 0 && (
          <p className="text-xs text-green-500 mt-2">Średnia: {Math.round(stats.average_optimization_score || 0)}%</p>
        )}
      </Link>
    </div>
  )
}
