// frontend/src/app/optimize/components/HistoryCompare.tsx
// Purpose: Before/After diff viewer for optimization history — side-by-side comparison
// NOT for: Running optimizations or loading results into form (those are HistoryTab/SingleTab)

'use client'

import { X, ArrowRight, TrendingUp, Shield, Zap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { OptimizationHistoryDetail } from '@/lib/types'

interface HistoryCompareProps {
  detail: OptimizationHistoryDetail
  onClose: () => void
}

export function HistoryCompare({ detail, onClose }: HistoryCompareProps) {
  const req = detail.request_data
  const resp = detail.response_data
  const listing = resp.listing
  const scores = resp.scores
  const juice = resp.ranking_juice

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Porownanie: {detail.product_title}
          </h3>
          <p className="text-xs text-gray-500">
            {new Date(detail.created_at).toLocaleDateString('pl-PL', {
              day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
            })}
            {' · '}{detail.marketplace} · {detail.mode}
            {resp.llm_provider && ` · ${resp.llm_provider}`}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Score summary bar */}
      <div className="flex flex-wrap gap-3">
        <ScoreBadge
          icon={<TrendingUp className="h-3 w-3" />}
          label="Pokrycie"
          value={`${scores?.coverage_pct ?? 0}%`}
          color={
            (scores?.coverage_pct ?? 0) >= 96 ? 'green' :
            (scores?.coverage_pct ?? 0) >= 82 ? 'yellow' : 'red'
          }
        />
        {juice && (
          <ScoreBadge
            icon={<Zap className="h-3 w-3" />}
            label="Ranking Juice"
            value={`${juice.score}/100 (${juice.grade})`}
            color={juice.score >= 70 ? 'green' : juice.score >= 40 ? 'yellow' : 'red'}
          />
        )}
        <ScoreBadge
          icon={<Shield className="h-3 w-3" />}
          label="Zgodnosc"
          value={detail.compliance_status}
          color={
            detail.compliance_status === 'PASS' ? 'green' :
            detail.compliance_status === 'WARNING' ? 'yellow' : 'red'
          }
        />
        {scores?.backend_utilization_pct !== undefined && (
          <ScoreBadge
            icon={<Zap className="h-3 w-3" />}
            label="Backend"
            value={`${scores.backend_utilization_pct}% (${scores.backend_byte_size}/249B)`}
            color={scores.backend_utilization_pct >= 80 ? 'green' : scores.backend_utilization_pct >= 50 ? 'yellow' : 'red'}
          />
        )}
      </div>

      {/* Side-by-side: Input → Output */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* LEFT: Input (Before) */}
        <Card className="border-gray-800">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-400">
              <div className="h-2 w-2 rounded-full bg-gray-500" />
              Dane wejsciowe (Before)
            </div>

            <CompareSection label="Tytul produktu" before={req.product_title} />
            <CompareSection label="Marka" before={req.brand} />

            {req.keywords && req.keywords.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500">Slowa kluczowe ({req.keywords.length})</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {req.keywords.map((kw, i) => (
                    <span key={i} className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-300">
                      {kw.phrase}
                      {kw.search_volume > 0 && (
                        <span className="ml-1 text-gray-500">{kw.search_volume.toLocaleString()}</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {req.original_description && (
              <CompareSection label="Oryginalny opis" before={req.original_description} maxLines={4} />
            )}
            {req.original_bullets && req.original_bullets.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500">Oryginalne bullety ({req.original_bullets.length})</span>
                <div className="mt-1 space-y-1">
                  {req.original_bullets.map((b, i) => (
                    <div key={i} className="rounded bg-gray-800/50 px-3 py-1.5 text-xs text-gray-400">{b}</div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* RIGHT: Output (After) */}
        <Card className="border-cyan-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-cyan-400">
              <div className="h-2 w-2 rounded-full bg-cyan-500" />
              Wygenerowany listing (After)
            </div>

            <CompareSection
              label="Tytul"
              after={listing.title}
              charCount={listing.title.length}
              maxChars={200}
            />

            {listing.bullet_points.length > 0 && (
              <div>
                <span className="text-xs font-medium text-gray-500">
                  Bullet Points ({listing.bullet_points.length})
                </span>
                <div className="mt-1 space-y-1">
                  {listing.bullet_points.map((b, i) => (
                    <div key={i} className="rounded bg-cyan-500/5 border border-cyan-500/10 px-3 py-1.5 text-xs text-white">
                      {b}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <CompareSection
              label="Opis"
              after={stripHtml(listing.description)}
              charCount={listing.description.length}
              maxChars={2000}
              maxLines={6}
            />

            <CompareSection
              label="Backend Keywords"
              after={listing.backend_keywords}
              charCount={new TextEncoder().encode(listing.backend_keywords).length}
              maxChars={249}
              unitLabel="B"
              mono
            />
          </CardContent>
        </Card>
      </div>

      {/* Keyword coverage breakdown */}
      {(resp.keyword_intel?.missing_keywords?.length > 0 || (req.keywords && req.keywords.length > 0)) && (
        <Card className="border-gray-800">
          <CardContent className="p-4">
            <span className="text-xs font-medium text-gray-500">
              Pokrycie slow kluczowych ({resp.keyword_intel?.total_analyzed ?? 0} przeanalizowanych)
            </span>
            <div className="mt-2 flex flex-wrap gap-1">
              {req.keywords?.filter((kw) =>
                !resp.keyword_intel?.missing_keywords?.includes(kw.phrase)
              ).map((kw, i: number) => (
                <span key={`f-${i}`} className="rounded bg-green-500/10 px-2 py-0.5 text-xs text-green-400">
                  {kw.phrase}
                </span>
              ))}
              {resp.keyword_intel?.missing_keywords?.map((kw: string, i: number) => (
                <span key={`m-${i}`} className="rounded bg-red-500/10 px-2 py-0.5 text-xs text-red-400 line-through">
                  {kw}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function CompareSection({
  label, before, after, charCount, maxChars, unitLabel = 'zn', maxLines, mono,
}: {
  label: string
  before?: string
  after?: string
  charCount?: number
  maxChars?: number
  unitLabel?: string
  maxLines?: number
  mono?: boolean
}) {
  const text = after || before || ''
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500">{label}</span>
        {charCount !== undefined && maxChars && (
          <span className={cn(
            'text-[10px]',
            charCount > maxChars ? 'text-red-400' : 'text-gray-600'
          )}>
            {charCount}/{maxChars} {unitLabel}
          </span>
        )}
      </div>
      <div className={cn(
        'mt-1 rounded bg-[#1A1A1A] px-3 py-2 text-xs text-white',
        mono && 'font-mono text-[11px]',
        maxLines && `line-clamp-${maxLines}`,
      )}>
        {text || <span className="text-gray-600 italic">brak</span>}
      </div>
    </div>
  )
}

function ScoreBadge({
  icon, label, value, color,
}: {
  icon: React.ReactNode
  label: string
  value: string
  color: 'green' | 'yellow' | 'red'
}) {
  const colors = {
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
    yellow: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
  }
  return (
    <div className={cn('flex items-center gap-1.5 rounded-lg border px-3 py-1.5', colors[color])}>
      {icon}
      <span className="text-[10px] text-gray-500">{label}:</span>
      <span className="text-xs font-medium">{value}</span>
    </div>
  )
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').trim()
}
