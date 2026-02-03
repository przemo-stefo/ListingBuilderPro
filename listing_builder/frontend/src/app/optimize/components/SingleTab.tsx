// frontend/src/app/optimize/components/SingleTab.tsx
// Purpose: Single-product listing optimizer form — extracted from page.tsx
// NOT for: Batch optimization (that's BatchTab.tsx)

'use client'

import { useState } from 'react'
import {
  Sparkles,
  Loader2,
  ChevronDown,
  ChevronRight,
  XCircle,
  FileText,
  Hash,
  Zap,
  Target,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useGenerateListing } from '@/lib/hooks/useOptimizer'
import { ScoresCard, ListingCard, KeywordIntelCard } from './ResultDisplay'
import type { OptimizerRequest, OptimizerResponse, OptimizerKeyword } from '@/lib/types'

// WHY: Marketplace options match what the n8n workflow supports
const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

export default function SingleTab() {
  // Form state
  const [productTitle, setProductTitle] = useState('')
  const [brand, setBrand] = useState('')
  const [productLine, setProductLine] = useState('')
  const [keywordsText, setKeywordsText] = useState('')
  const [marketplace, setMarketplace] = useState('amazon_de')
  const [mode, setMode] = useState<'aggressive' | 'standard'>('aggressive')

  // Results
  const [results, setResults] = useState<OptimizerResponse | null>(null)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  // Collapsible sections
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [asin, setAsin] = useState('')
  const [category, setCategory] = useState('')

  // Hook
  const generateMutation = useGenerateListing()

  // WHY: Parse keywords from textarea — supports CSV (phrase,volume) and plain text (one per line)
  const parseKeywords = (): OptimizerKeyword[] => {
    return keywordsText
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => {
        // Try CSV format: "keyword phrase,1234"
        const commaIdx = line.lastIndexOf(',')
        if (commaIdx > 0) {
          const phrase = line.substring(0, commaIdx).trim().replace(/^["']|["']$/g, '')
          const vol = parseInt(line.substring(commaIdx + 1).trim())
          if (!isNaN(vol) && vol > 0) {
            return { phrase, search_volume: vol }
          }
        }
        // Plain text — no volume
        return { phrase: line.replace(/^["']|["']$/g, ''), search_volume: 0 }
      })
  }

  const keywordCount = parseKeywords().length
  const canSubmit = productTitle.length >= 3 && brand.length >= 1 && keywordCount >= 1

  const handleGenerate = () => {
    const payload: OptimizerRequest = {
      product_title: productTitle,
      brand,
      product_line: productLine || undefined,
      keywords: parseKeywords(),
      marketplace,
      mode,
      asin: asin || undefined,
      category: category || undefined,
    }

    generateMutation.mutate(payload, {
      onSuccess: (data) => {
        setResults(data)
      },
    })
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const isLoading = generateMutation.isPending

  return (
    <div className="space-y-6">
      {/* Section 1: Product Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Product Info</CardTitle>
          </div>
          <CardDescription>Basic product information for the listing</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Product Title <span className="text-red-400">*</span>
            </label>
            <Input
              value={productTitle}
              onChange={(e) => setProductTitle(e.target.value)}
              placeholder="e.g. Silicone Kitchen Utensil Set 12-Piece"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Brand <span className="text-red-400">*</span>
              </label>
              <Input
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="e.g. ZULAY"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Product Line</label>
              <Input
                value={productLine}
                onChange={(e) => setProductLine(e.target.value)}
                placeholder="e.g. Premium Kitchen (optional)"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Keywords */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Hash className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Keywords</CardTitle>
          </div>
          <CardDescription>
            Paste keywords, one per line. Optionally add search volume after a comma.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <textarea
            value={keywordsText}
            onChange={(e) => setKeywordsText(e.target.value)}
            placeholder={
              'silicone kitchen utensils,12000\nkitchen utensil set,8500\ncooking utensils silicone,6200\nheat resistant spatula,3400\nnon stick cooking tools'
            }
            rows={8}
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
          />
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>
              {keywordCount} keyword{keywordCount !== 1 ? 's' : ''} detected
            </span>
            <span>Format: keyword phrase,search_volume (volume optional)</span>
          </div>
        </CardContent>
      </Card>

      {/* Section 3: Marketplace & Mode */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Target & Mode</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-gray-400">Marketplace</label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              {MARKETPLACES.map((mp) => (
                <button
                  key={mp.id}
                  onClick={() => setMarketplace(mp.id)}
                  className={cn(
                    'rounded-lg border px-3 py-2 text-sm transition-colors',
                    marketplace === mp.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                  )}
                >
                  <span className="mr-1 text-xs">{mp.flag}</span>
                  {mp.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-400">Optimization Mode</label>
            <div className="flex gap-2">
              <button
                onClick={() => setMode('aggressive')}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                  mode === 'aggressive'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                <Zap className="h-4 w-4" />
                Aggressive
                <span className="text-[10px] text-gray-500">96%+ coverage</span>
              </button>
              <button
                onClick={() => setMode('standard')}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                  mode === 'standard'
                    ? 'border-white bg-white/5 text-white'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                <Target className="h-4 w-4" />
                Standard
                <span className="text-[10px] text-gray-500">82%+ coverage</span>
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 4: Advanced (collapsible) */}
      <Card>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex w-full items-center justify-between p-6"
        >
          <div>
            <h3 className="text-lg font-semibold text-white">Advanced</h3>
            <p className="text-sm text-gray-400">ASIN, category (optional)</p>
          </div>
          {showAdvanced ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {showAdvanced && (
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">ASIN</label>
              <Input
                value={asin}
                onChange={(e) => setAsin(e.target.value)}
                placeholder="B0XXXXXXXX"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">Category</label>
              <Input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Kitchen & Dining"
              />
            </div>
          </CardContent>
        )}
      </Card>

      {/* Generate Button */}
      <div className="flex items-center gap-3">
        <Button onClick={handleGenerate} disabled={!canSubmit || isLoading} size="lg">
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          {isLoading ? 'Generating listing...' : 'Generate Optimized Listing'}
        </Button>
        {isLoading && (
          <span className="text-xs text-gray-500">
            AI is writing title, bullets, and description...
          </span>
        )}
      </div>

      {/* Results */}
      {results && results.status === 'completed' && (
        <div className="space-y-4">
          <ScoresCard scores={results.scores} intel={results.keyword_intel} />
          <ListingCard
            listing={results.listing}
            compliance={results.compliance}
            copiedField={copiedField}
            onCopy={copyToClipboard}
          />
          <KeywordIntelCard intel={results.keyword_intel} />
        </div>
      )}

      {results && results.status === 'error' && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-red-400">
              <XCircle className="h-5 w-5" />
              <span>Optimization failed. Check n8n workflow logs.</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
