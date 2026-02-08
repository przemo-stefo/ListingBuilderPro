// frontend/src/app/optimize/page.tsx
// Purpose: Listing Optimizer page — orchestrator with Single/Batch/History tab switching
// NOT for: Form logic or result display (those are in components/)

'use client'

import { useState } from 'react'
import { Layers, FileText, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import SingleTab from './components/SingleTab'
import BatchTab from './components/BatchTab'
import HistoryTab from './components/HistoryTab'
import type { OptimizerResponse } from '@/lib/types'

type Tab = 'single' | 'batch' | 'history'

export default function OptimizePage() {
  const [activeTab, setActiveTab] = useState<Tab>('single')
  // WHY: When user clicks "Load" in History, we switch to Single and pass the result
  const [loadedResult, setLoadedResult] = useState<OptimizerResponse | null>(null)

  const handleLoadFromHistory = (result: OptimizerResponse) => {
    setLoadedResult(result)
    setActiveTab('single')
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
            onClick={() => setActiveTab('history')}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'history'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Clock className="h-4 w-4" />
            History
          </button>
        </div>
      </div>

      {/* Active tab content */}
      {activeTab === 'single' && <SingleTab loadedResult={loadedResult} />}
      {activeTab === 'batch' && <BatchTab />}
      {activeTab === 'history' && <HistoryTab onLoadResult={handleLoadFromHistory} />}
    </div>
  )
}
