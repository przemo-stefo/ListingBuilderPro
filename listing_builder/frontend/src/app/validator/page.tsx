// frontend/src/app/validator/page.tsx
// Purpose: Product Validator page — AI rates product potential 1-10 with 6 dimensions
// NOT for: Listing scoring (listing-score/) or ad copy (ad-copy/)

'use client'

import { useState } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PremiumGate } from '@/components/tier/PremiumGate'
import { ValidatorForm } from './components/ValidatorForm'
import { ValidatorResult } from './components/ValidatorResult'
import { ValidatorHistory } from './components/ValidatorHistory'
import { analyzeProduct } from '@/lib/api/validator'
import type { ValidatorResponse } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'

type Tab = 'analyze' | 'history'

export default function ValidatorPage() {
  const [activeTab, setActiveTab] = useState<Tab>('analyze')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ValidatorResponse | null>(null)
  const [error, setError] = useState('')

  const handleAnalyze = async (productInput: string, marketplace: string) => {
    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await analyzeProduct(productInput, marketplace)
      setResult(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : typeof e === 'object' && e !== null && 'message' in e ? String((e as Record<string, unknown>).message) : 'Nieznany błąd'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PremiumGate feature="Walidator Produktu">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Search className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Walidator Produktu</h1>
            <p className="text-xs text-gray-400">Sprawdź potencjał sprzedażowy produktu zanim zainwestujesz</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#121212] p-1">
          {([
            { key: 'analyze' as Tab, label: 'Analiza' },
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
        {activeTab === 'analyze' && (
          <div className="space-y-4">
            <ValidatorForm onSubmit={handleAnalyze} isLoading={isLoading} />

            {error && (
              <Card className="border-gray-800">
                <CardContent className="p-4">
                  <p className="text-sm text-red-400">{error}</p>
                </CardContent>
              </Card>
            )}

            {result && <ValidatorResult result={result} />}
          </div>
        )}

        {activeTab === 'history' && <ValidatorHistory />}
      </div>
    </PremiumGate>
  )
}
