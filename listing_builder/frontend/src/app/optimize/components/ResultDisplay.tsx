// frontend/src/app/optimize/components/ResultDisplay.tsx
// Purpose: Shared result display components — ScoresCard, ListingCard, KeywordIntelCard
// NOT for: Form logic or data fetching (those are in SingleTab/BatchTab)

'use client'

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  Download,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { OptimizerResponse } from '@/lib/types'

// WHY: Client-side CSV export — no backend needed, data already in memory
export function downloadCSV(response: OptimizerResponse) {
  const { listing, scores, compliance, marketplace, brand } = response
  const headers = ['Title', 'Bullet 1', 'Bullet 2', 'Bullet 3', 'Bullet 4', 'Bullet 5', 'Description', 'Backend Keywords', 'Coverage %', 'Compliance', 'Marketplace', 'Brand']
  const esc = (v: string) => `"${v.replace(/"/g, '""')}"`
  const bullets = [...listing.bullet_points]
  while (bullets.length < 5) bullets.push('')
  const row = [listing.title, ...bullets.slice(0, 5), listing.description, listing.backend_keywords, String(scores.coverage_pct), compliance.status, marketplace, brand].map(esc)
  const csv = [headers.join(','), row.join(',')].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `listing_${brand}_${marketplace}_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// WHY: Separate component for scores to keep result display clean
export function ScoresCard({
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
export function ListingCard({
  listing,
  compliance,
  copiedField,
  onCopy,
  fullResponse,
}: {
  listing: OptimizerResponse['listing']
  compliance: OptimizerResponse['compliance']
  copiedField: string | null
  onCopy: (text: string, field: string) => void
  fullResponse?: OptimizerResponse
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Generated Listing</CardTitle>
          <div className="flex items-center gap-2">
            {fullResponse && (
              <Button variant="outline" size="sm" onClick={() => downloadCSV(fullResponse)}>
                <Download className="mr-1 h-3 w-3" />
                CSV
              </Button>
            )}
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

export function CopyButton({
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
export function KeywordIntelCard({ intel }: { intel: OptimizerResponse['keyword_intel'] }) {
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
