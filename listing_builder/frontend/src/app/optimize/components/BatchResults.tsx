// frontend/src/app/optimize/components/BatchResults.tsx
// Purpose: Display batch optimization results — collapsible cards with scores + download CSV
// NOT for: Single product results (those use ResultDisplay components directly)

'use client'

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Download,
  RotateCcw,
  CheckCircle,
  XCircle,
  Copy,
  Check,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { exportResultsCSV } from '@/lib/utils/csvParser'
import { ScoresCard, ListingCard, KeywordIntelCard } from './ResultDisplay'
import type { BatchOptimizerResponse, BatchOptimizerResult } from '@/lib/types'

interface BatchResultsProps {
  response: BatchOptimizerResponse
  onReset: () => void
}

export default function BatchResults({ response, onReset }: BatchResultsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index)
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <Card>
        <CardContent className="flex items-center justify-between p-4">
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              <span className="text-white font-medium">{response.total}</span> products processed
            </div>
            <Badge
              variant="secondary"
              className="bg-green-500/10 text-green-400"
            >
              {response.succeeded} succeeded
            </Badge>
            {response.failed > 0 && (
              <Badge
                variant="secondary"
                className="bg-red-500/10 text-red-400"
              >
                {response.failed} failed
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            {response.succeeded > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => exportResultsCSV(response)}
              >
                <Download className="mr-2 h-4 w-4" />
                Download All as CSV
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={onReset}>
              <RotateCcw className="mr-2 h-4 w-4" />
              New Batch
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Product cards */}
      {response.results.map((item, index) => (
        <ProductResultCard
          key={index}
          item={item}
          index={index}
          isExpanded={expandedIndex === index}
          onToggle={() => toggleExpand(index)}
          copiedField={copiedField}
          onCopy={copyToClipboard}
        />
      ))}
    </div>
  )
}

// WHY: Each product gets a collapsible card showing title + score badge
function ProductResultCard({
  item,
  index,
  isExpanded,
  onToggle,
  copiedField,
  onCopy,
}: {
  item: BatchOptimizerResult
  index: number
  isExpanded: boolean
  onToggle: () => void
  copiedField: string | null
  onCopy: (text: string, field: string) => void
}) {
  const isSuccess = item.status === 'completed' && item.result
  const coverage = item.result?.scores.coverage_pct ?? 0

  const coverageBadgeColor =
    coverage >= 96
      ? 'bg-green-500/10 text-green-400'
      : coverage >= 82
        ? 'bg-yellow-500/10 text-yellow-400'
        : 'bg-red-500/10 text-red-400'

  return (
    <Card>
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          {isSuccess ? (
            <CheckCircle className="h-5 w-5 shrink-0 text-green-400" />
          ) : (
            <XCircle className="h-5 w-5 shrink-0 text-red-400" />
          )}
          <div>
            <p className="text-sm font-medium text-white">
              {index + 1}. {item.product_title}
            </p>
            {!isSuccess && item.error && (
              <p className="text-xs text-red-400">{item.error}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isSuccess && (
            <Badge variant="secondary" className={cn('text-xs', coverageBadgeColor)}>
              {coverage}% coverage
            </Badge>
          )}
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {/* WHY: Expanded view reuses the shared display components */}
      {isExpanded && isSuccess && item.result && (
        <CardContent className="space-y-4 border-t border-gray-800 pt-4">
          <ScoresCard scores={item.result.scores} intel={item.result.keyword_intel} />
          <ListingCard
            listing={item.result.listing}
            compliance={item.result.compliance}
            copiedField={copiedField}
            onCopy={(text, field) => onCopy(text, `${index}-${field}`)}
          />
          <KeywordIntelCard intel={item.result.keyword_intel} />
        </CardContent>
      )}
    </Card>
  )
}
