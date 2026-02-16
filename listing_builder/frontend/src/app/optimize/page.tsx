// frontend/src/app/optimize/page.tsx
// Purpose: Listing Optimizer page — orchestrator with Single/Batch/History tab switching
// NOT for: Form logic or result display (those are in components/)

'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layers, FileText, Clock, Crown, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useToast } from '@/lib/hooks/useToast'
import SingleTab from './components/SingleTab'
import BatchTab from './components/BatchTab'
import HistoryTab from './components/HistoryTab'
import type { OptimizerResponse } from '@/lib/types'

type Tab = 'single' | 'batch' | 'history'

// WHY: Next.js 14 requires Suspense boundary around useSearchParams()
function OptimizeContent() {
  const searchParams = useSearchParams()
  // WHY: Allegro Manager "Optymalizuj z AI" passes ?prefill=title
  const prefillTitle = searchParams.get('prefill') ?? undefined
  const [activeTab, setActiveTab] = useState<Tab>('single')
  // WHY: When user clicks "Load" in History, we switch to Single and pass the result
  const [loadedResult, setLoadedResult] = useState<OptimizerResponse | null>(null)
  const { isPremium } = useTier()
  const { toast } = useToast()

  const handleLoadFromHistory = (result: OptimizerResponse) => {
    setLoadedResult(result)
    setActiveTab('single')
  }

  const handleHistoryClick = () => {
    if (!isPremium) {
      toast({
        title: 'Historia — Premium',
        description: 'Historia optymalizacji jest dostepna w planie Premium.',
        variant: 'destructive',
      })
      return
    }
    setActiveTab('history')
  }

  return (
    <div className="space-y-6">
      {/* Page header + tab toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Listing Optimizer</h1>
          <p className="text-sm text-gray-400">
            Generate SEO-optimized titles, bullets, descriptions, and backend keywords
          </p>
        </div>

        {/* Tab toggle */}
        <div className="flex rounded-lg border border-gray-800 p-1">
          <button
            onClick={() => { setActiveTab('single'); setLoadedResult(null) }}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'single'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <FileText className="h-4 w-4" />
            Single
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'batch'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Layers className="h-4 w-4" />
            Batch
          </button>
          <button
            onClick={handleHistoryClick}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'history'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Clock className="h-4 w-4" />
            History
            {!isPremium && <Crown className="h-3 w-3 text-amber-400" />}
          </button>
        </div>
      </div>

      {/* Active tab content */}
      {activeTab === 'single' && <SingleTab loadedResult={loadedResult} initialTitle={prefillTitle} />}
      {activeTab === 'batch' && <BatchTab />}
      {activeTab === 'history' && isPremium && <HistoryTab onLoadResult={handleLoadFromHistory} />}
    </div>
  )
}

export default function OptimizePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    }>
      <OptimizeContent />
    </Suspense>
  )
}
