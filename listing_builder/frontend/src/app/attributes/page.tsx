// frontend/src/app/attributes/page.tsx
// Purpose: Auto-Atrybuty page shell — generate Allegro product attributes via AI
// NOT for: Listing optimization (optimizer/) or product validation (validator/)

'use client'

import { useState } from 'react'
import { Tags } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AttributeForm } from './components/AttributeForm'
import { AttributeResult } from './components/AttributeResult'
import { AttributeHistory } from './components/AttributeHistory'
import { generateAttributes } from '@/lib/api/attributes'
import type { AttributeRunResponse } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'

type Tab = 'generate' | 'history'

export default function AttributesPage() {
  const [activeTab, setActiveTab] = useState<Tab>('generate')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<AttributeRunResponse | null>(null)
  const [error, setError] = useState('')

  const handleGenerate = async (
    productInput: string,
    categoryId: string,
    categoryName: string,
    categoryPath: string,
  ) => {
    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await generateAttributes(productInput, categoryId, categoryName, categoryPath)
      setResult(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : typeof e === 'object' && e !== null && 'message' in e ? String((e as Record<string, unknown>).message) : 'Nieznany błąd'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-blue-500/20 p-2">
          <Tags className="h-6 w-6 text-blue-400" />
        </div>
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-white">Auto-Atrybuty</h1>
            <p className="text-xs text-gray-400">Wygeneruj atrybuty produktowe zgodne z marketplace</p>
          </div>
          <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-400">BETA</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#121212] p-1">
        {([
          { key: 'generate' as Tab, label: 'Generuj' },
          { key: 'history' as Tab, label: 'Historia' },
        ]).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-[#1A1A1A] text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'generate' && (
        <div className="space-y-4">
          <AttributeForm onSubmit={handleGenerate} isLoading={isLoading} />

          {error && (
            <Card className="border-gray-800">
              <CardContent className="p-4">
                <p className="text-sm text-red-400">{error}</p>
              </CardContent>
            </Card>
          )}

          {result && <AttributeResult result={result} />}
        </div>
      )}

      {activeTab === 'history' && <AttributeHistory />}
    </div>
  )
}
