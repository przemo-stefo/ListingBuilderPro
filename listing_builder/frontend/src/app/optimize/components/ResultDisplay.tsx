// frontend/src/app/optimize/components/ResultDisplay.tsx
// Purpose: Shared result display utilities — CSV exports, ScoresCard, CopyButton, ListingSection
// NOT for: Large standalone components (those are in separate files)

'use client'

import { Copy, Check } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { OptimizerResponse } from '@/lib/types'

// WHY: Map marketplace to eBay SiteID — each eBay market has a different numeric ID
function getEbaySiteId(marketplace: string): number {
  if (marketplace.includes('us')) return 0
  if (marketplace.includes('uk')) return 3
  return 77 // DE = default
}

// WHY: eBay File Exchange CSV — frontend-only, data already in browser
export function downloadEbayCsv(response: OptimizerResponse) {
  const { listing, brand, marketplace } = response
  const siteId = getEbaySiteId(marketplace)
  const esc = (v: string) => `"${v.replace(/"/g, '""')}"`
  const headers = [`*Action(SiteID=${siteId})`, 'Title', 'Description', 'ConditionID', 'Format', 'Duration']
  const row = ['Add', listing.title, listing.description, '1000', 'FixedPrice', 'GTC'].map(esc)
  const csv = [headers.join(','), row.join(',')].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ebay_listing_${brand}_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

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

// WHY: Reusable section for title/description/backend with copy + char count
export function ListingSection({
  label, content, charCount, maxChars, unitLabel = 'chars',
  field, copiedField, onCopy, multiline = false, mono = false, isHtml = false,
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
  isHtml?: boolean
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
      {isHtml && content ? (
        <div
          className="listing-html rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-2 [&_li]:mb-1 [&_b]:font-semibold [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-1"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      ) : (
        <div
          className={cn(
            'rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white',
            multiline && 'whitespace-pre-wrap',
            mono && 'font-mono text-xs'
          )}
        >
          {content || '—'}
        </div>
      )}
    </div>
  )
}

export function CopyButton({
  text, field, copiedField, onCopy,
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
