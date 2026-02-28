// frontend/src/components/ui/ActivityFeed.tsx
// Purpose: Last 5 optimization activities on dashboard
// NOT for: Full history view (that's optimize/HistoryTab)

'use client'

import Link from 'next/link'
import { Sparkles, Clock, AlertCircle } from 'lucide-react'
import { useHistoryList } from '@/lib/hooks/useOptimizerHistory'
import { formatRelativeTime, truncate } from '@/lib/utils'

export function ActivityFeed() {
  const { data, isLoading, error } = useHistoryList(1)

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <h3 className="text-sm font-semibold text-white mb-3">Ostatnia aktywność</h3>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-800 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // WHY: Graceful degradation — don't break dashboard if history API fails
  if (error) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <h3 className="text-sm font-semibold text-white mb-3">Ostatnia aktywność</h3>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>Nie udało się załadować historii</span>
        </div>
      </div>
    )
  }

  const items = data?.items?.slice(0, 5) ?? []

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Ostatnia aktywność</h3>
        {items.length > 0 && (
          <Link href="/optimize" className="text-xs text-gray-500 hover:text-white transition-colors">
            Zobacz wszystko
          </Link>
        )}
      </div>

      {items.length === 0 ? (
        <div className="text-center py-4">
          <Clock className="mx-auto h-8 w-8 text-gray-700 mb-2" />
          <p className="text-xs text-gray-500">Brak aktywności — zaimportuj pierwszy produkt</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center gap-3 rounded-lg p-2 hover:bg-white/5 transition-colors">
              <Sparkles className="h-4 w-4 text-blue-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">
                  {truncate(item.product_title, 50)}
                </p>
                <p className="text-xs text-gray-500">
                  {item.marketplace} • {item.mode}
                </p>
              </div>
              <span className="text-xs text-gray-600 shrink-0">
                {formatRelativeTime(item.created_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
