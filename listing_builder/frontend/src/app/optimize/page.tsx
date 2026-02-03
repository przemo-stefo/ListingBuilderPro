// frontend/src/app/optimize/page.tsx
// Purpose: Listing Optimizer page — generate SEO-optimized listings via n8n workflow
// NOT for: Batch optimization of existing products (that was the old page)

'use client'

import { useState } from 'react'
import {
  Sparkles,
  Loader2,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  Zap,
  Target,
  FileText,
  Hash,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useGenerateListing } from '@/lib/hooks/useOptimizer'
import type { OptimizerRequest, OptimizerResponse, OptimizerKeyword } from '@/lib/types'

// WHY: Marketplace options match what the n8n workflow supports
const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

export default function OptimizePage() {
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
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Listing Optimizer</h1>
        <p className="text-sm text-gray-400">
          Generate SEO-optimized titles, bullets, descriptions, and backend keywords
        </p>
      </div>

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
          {/* Marketplace selector */}
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

          {/* Mode toggle */}
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

      {/* Section 5: Results */}
      {results && results.status === 'completed' && (
        <div className="space-y-4">
          {/* Scores overview */}
          <ScoresCard scores={results.scores} intel={results.keyword_intel} />

          {/* Generated listing */}
          <ListingCard
            listing={results.listing}
            compliance={results.compliance}
            copiedField={copiedField}
            onCopy={copyToClipboard}
          />

          {/* Keyword intel */}
          <KeywordIntelCard intel={results.keyword_intel} />
        </div>
      )}

      {/* Error state */}
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

// WHY: Separate component for scores to keep the page clean
function ScoresCard({
  scores,
  intel,
}: {
  scores: OptimizerResponse['scores']
  intel: OptimizerResponse['keyword_intel']
}) {
  const coverageColor =
    scores.coverage_pct >= 96
      ? 'text-green-400'
      : scores.coverage_pct >= 82
        ? 'text-yellow-400'
        : 'text-red-400'

  const complianceColor =
    scores.compliance_status === 'PASS'
      ? 'text-green-400'
      : scores.compliance_status === 'WARNING'
        ? 'text-yellow-400'
        : 'text-red-400'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Optimization Scores</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
            <p className="text-xs text-gray-500">Keyword Coverage</p>
            <p className={cn('text-2xl font-bold', coverageColor)}>
              {scores.coverage_pct}%
            </p>
            <Badge
              variant="secondary"
              className={cn(
                'mt-1 text-[10px]',
                scores.coverage_mode === 'AGGRESSIVE'
                  ? 'bg-green-500/10 text-green-400'
                  : scores.coverage_mode === 'STANDARD'
                    ? 'bg-yellow-500/10 text-yellow-400'
                    : 'bg-red-500/10 text-red-400'
              )}
            >
              {scores.coverage_mode}
            </Badge>
          </div>

          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
            <p className="text-xs text-gray-500">Exact Matches in Title</p>
            <p className="text-2xl font-bold text-white">{scores.exact_matches_in_title}</p>
            <p className="mt-1 text-[10px] text-gray-500">keyword phrases</p>
          </div>

          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
            <p className="text-xs text-gray-500">Backend Utilization</p>
            <p className="text-2xl font-bold text-white">{scores.backend_utilization_pct}%</p>
            <p className="mt-1 text-[10px] text-gray-500">
              {scores.backend_byte_size} / 249 bytes
            </p>
          </div>

          <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-4">
            <p className="text-xs text-gray-500">Compliance</p>
            <p className={cn('text-2xl font-bold', complianceColor)}>
              {scores.compliance_status}
            </p>
            <p className="mt-1 text-[10px] text-gray-500">
              {intel.total_analyzed} keywords analyzed
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// WHY: Listing card with copy buttons for each section
function ListingCard({
  listing,
  compliance,
  copiedField,
  onCopy,
}: {
  listing: OptimizerResponse['listing']
  compliance: OptimizerResponse['compliance']
  copiedField: string | null
  onCopy: (text: string, field: string) => void
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Generated Listing</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const full = [
                `TITLE:\n${listing.title}`,
                `\nBULLET POINTS:\n${listing.bullet_points.join('\n')}`,
                `\nDESCRIPTION:\n${listing.description}`,
                `\nBACKEND KEYWORDS:\n${listing.backend_keywords}`,
              ].join('\n')
              onCopy(full, 'all')
            }}
          >
            {copiedField === 'all' ? (
              <Check className="mr-1 h-3 w-3" />
            ) : (
              <Copy className="mr-1 h-3 w-3" />
            )}
            Copy All
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Title */}
        <ListingSection
          label="Title"
          content={listing.title}
          charCount={listing.title.length}
          maxChars={200}
          field="title"
          copiedField={copiedField}
          onCopy={onCopy}
        />

        {/* Bullet Points */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-300">Bullet Points</h3>
              <span className="text-xs text-gray-500">
                {listing.bullet_points.length} bullets
              </span>
            </div>
            <CopyButton
              text={listing.bullet_points.join('\n')}
              field="bullets"
              copiedField={copiedField}
              onCopy={onCopy}
            />
          </div>
          <div className="space-y-2">
            {listing.bullet_points.map((bullet, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white"
              >
                {bullet}
              </div>
            ))}
          </div>
        </div>

        {/* Description */}
        <ListingSection
          label="Description"
          content={listing.description}
          charCount={listing.description.length}
          maxChars={2000}
          field="description"
          copiedField={copiedField}
          onCopy={onCopy}
          multiline
        />

        {/* Backend Keywords */}
        <ListingSection
          label="Backend Keywords"
          content={listing.backend_keywords}
          charCount={new TextEncoder().encode(listing.backend_keywords).length}
          maxChars={249}
          unitLabel="bytes"
          field="backend"
          copiedField={copiedField}
          onCopy={onCopy}
          mono
        />

        {/* Compliance warnings/errors */}
        {(compliance.errors.length > 0 || compliance.warnings.length > 0) && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Compliance Notes</h3>
            {compliance.errors.map((err, i) => (
              <div
                key={`e-${i}`}
                className="flex items-start gap-2 rounded bg-red-500/10 px-3 py-2 text-xs text-red-400"
              >
                <XCircle className="mt-0.5 h-3 w-3 shrink-0" />
                {err}
              </div>
            ))}
            {compliance.warnings.map((warn, i) => (
              <div
                key={`w-${i}`}
                className="flex items-start gap-2 rounded bg-yellow-500/10 px-3 py-2 text-xs text-yellow-400"
              >
                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                {warn}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// WHY: Reusable section for title/description/backend with copy + char count
function ListingSection({
  label,
  content,
  charCount,
  maxChars,
  unitLabel = 'chars',
  field,
  copiedField,
  onCopy,
  multiline = false,
  mono = false,
}: {
  label: string
  content: string
  charCount: number
  maxChars: number
  unitLabel?: string
  field: string
  copiedField: string | null
  onCopy: (text: string, field: string) => void
  multiline?: boolean
  mono?: boolean
}) {
  const overLimit = charCount > maxChars

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-300">{label}</h3>
          <span className={cn('text-xs', overLimit ? 'text-red-400' : 'text-gray-500')}>
            {charCount} / {maxChars} {unitLabel}
          </span>
        </div>
        <CopyButton text={content} field={field} copiedField={copiedField} onCopy={onCopy} />
      </div>
      <div
        className={cn(
          'rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white',
          multiline && 'whitespace-pre-wrap',
          mono && 'font-mono text-xs'
        )}
      >
        {content || '—'}
      </div>
    </div>
  )
}

function CopyButton({
  text,
  field,
  copiedField,
  onCopy,
}: {
  text: string
  field: string
  copiedField: string | null
  onCopy: (text: string, field: string) => void
}) {
  return (
    <button
      onClick={() => onCopy(text, field)}
      className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
    >
      {copiedField === field ? (
        <>
          <Check className="h-3 w-3 text-green-400" />
          <span className="text-green-400">Copied</span>
        </>
      ) : (
        <>
          <Copy className="h-3 w-3" />
          Copy
        </>
      )}
    </button>
  )
}

// WHY: Shows keyword tier distribution and missing keywords
function KeywordIntelCard({ intel }: { intel: OptimizerResponse['keyword_intel'] }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Card>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-6"
      >
        <div>
          <h3 className="text-lg font-semibold text-white">Keyword Intelligence</h3>
          <p className="text-sm text-gray-400">
            {intel.total_analyzed} keywords analyzed across 3 tiers
          </p>
        </div>
        {expanded ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>
      {expanded && (
        <CardContent className="space-y-4">
          {/* Tier distribution */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-xs text-gray-500">Tier 1 (Title)</p>
              <p className="text-xl font-bold text-white">{intel.tier1_title}</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-xs text-gray-500">Tier 2 (Bullets)</p>
              <p className="text-xl font-bold text-white">{intel.tier2_bullets}</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-3 text-center">
              <p className="text-xs text-gray-500">Tier 3 (Backend)</p>
              <p className="text-xl font-bold text-white">{intel.tier3_backend}</p>
            </div>
          </div>

          {/* Missing keywords */}
          {intel.missing_keywords.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-300">
                Missing Keywords ({intel.missing_keywords.length})
              </h4>
              <div className="flex flex-wrap gap-1">
                {intel.missing_keywords.map((kw, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="bg-red-500/10 text-red-400 text-[10px]"
                  >
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Root words */}
          {intel.root_words.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-300">Top Root Words</h4>
              <div className="flex flex-wrap gap-1">
                {intel.root_words.map((rw, i) => (
                  <Badge key={i} variant="secondary" className="text-[10px]">
                    {rw.word} ({rw.frequency})
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
