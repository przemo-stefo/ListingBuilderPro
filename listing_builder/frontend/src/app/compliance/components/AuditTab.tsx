// frontend/src/app/compliance/components/AuditTab.tsx
// Purpose: Product card audit — URL input → scrape → compliance check → AI fix suggestions
// NOT for: File upload validation (that's UploadTab.tsx)

'use client'

import { useState } from 'react'
import {
  Search,
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Lightbulb,
  ExternalLink,
  Image as ImageIcon,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useAuditProduct } from '@/lib/hooks/useCompliance'
import type { AuditResult, AuditIssue } from '@/lib/api/compliance'

const MARKETPLACE_OPTIONS: { id: string; label: string; disabled?: boolean }[] = [
  { id: 'allegro', label: 'Allegro' },
  { id: 'amazon', label: 'Amazon (wkrótce)', disabled: true },
  { id: 'ebay', label: 'eBay (wkrótce)', disabled: true },
]

export default function AuditTab() {
  const [url, setUrl] = useState('')
  const [marketplace, setMarketplace] = useState('allegro')
  const auditMutation = useAuditProduct()

  const result = auditMutation.data as AuditResult | undefined

  const handleAudit = () => {
    if (!url.trim()) return
    auditMutation.mutate({ url: url.trim(), marketplace })
  }

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle className="h-5 w-5 text-green-400" />
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-400" />
      default: return <XCircle className="h-5 w-5 text-red-400" />
    }
  }

  const severityBadge = (severity: string) => {
    const colors = {
      error: 'bg-red-500/10 text-red-400 border-red-500/20',
      warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    }
    return colors[severity as keyof typeof colors] || colors.info
  }

  return (
    <div className="space-y-6">
      {/* Input section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Audyt karty produktu</CardTitle>
          <CardDescription>
            Wklej URL produktu — sprawdzimy zgodność i podpowiemy co poprawić
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            {MARKETPLACE_OPTIONS.map((mp) => (
              <button
                key={mp.id}
                onClick={() => !mp.disabled && setMarketplace(mp.id)}
                disabled={mp.disabled}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm transition-colors',
                  mp.disabled
                    ? 'border-gray-800 text-gray-600 cursor-not-allowed'
                    : marketplace === mp.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                )}
              >
                {mp.label}
              </button>
            ))}
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAudit()}
              placeholder="https://allegro.pl/oferta/..."
              className="flex-1 rounded-lg border border-gray-800 bg-[#121212] px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-green-500 focus:outline-none"
            />
            <Button
              onClick={handleAudit}
              disabled={!url.trim() || auditMutation.isPending}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {auditMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Search className="mr-2 h-4 w-4" />
              )}
              Audytuj
            </Button>
          </div>

          {auditMutation.isPending && (
            <p className="text-sm text-gray-400 animate-pulse">
              Scrapuję i analizuję kartę produktu...
            </p>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <>
          {/* Score + product info */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {statusIcon(result.overall_status)}
                  <div>
                    <h3 className="font-semibold text-white line-clamp-2">
                      {result.product_title || 'Brak tytułu'}
                    </h3>
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
                      <Badge variant="secondary" className="text-[10px]">{result.marketplace}</Badge>
                      {result.source_id && <span>ID: {result.source_id}</span>}
                      <a
                        href={result.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-gray-400 hover:text-white"
                      >
                        <ExternalLink className="h-3 w-3" /> Otwórz
                      </a>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn('text-3xl font-bold', scoreColor(result.score))}>
                    {result.score}
                  </p>
                  <p className="text-xs text-gray-500">/ 100</p>
                </div>
              </div>

              {/* Product data summary */}
              {result.product_data && (() => {
                const pd = result.product_data as Record<string, string | number | string[]>
                return (
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      { label: 'Cena', value: pd.price ? `${pd.price} ${pd.currency || 'PLN'}` : '—' },
                      { label: 'EAN', value: String(pd.ean || '—') },
                      { label: 'Marka', value: String(pd.brand || '—') },
                      { label: 'Parametry', value: `${pd.parameters_count || 0} wypełnionych` },
                    ].map((item) => (
                      <div key={item.label} className="rounded-lg border border-gray-800 bg-[#121212] p-3">
                        <p className="text-[10px] text-gray-500 uppercase">{item.label}</p>
                        <p className="text-sm text-white truncate">{item.value}</p>
                      </div>
                    ))}
                  </div>
                )
              })()}

              {/* Images + Parameters detail */}
              {result.product_data && (() => {
                const pd = result.product_data as Record<string, unknown>
                const images = Array.isArray(pd.images) ? pd.images as string[] : []
                const params = (typeof pd.parameters === 'object' && pd.parameters !== null)
                  ? pd.parameters as Record<string, string>
                  : {}
                const paramEntries = Object.entries(params)

                return (
                  <>
                    {images.length > 0 && (
                      <div className="mt-4 flex items-center gap-2">
                        <ImageIcon className="h-4 w-4 text-gray-500" />
                        <span className="text-xs text-gray-400">{images.length} zdjęć</span>
                      </div>
                    )}
                    {paramEntries.length > 0 && (
                      <details className="mt-4">
                        <summary className="cursor-pointer text-xs text-gray-400 hover:text-white">
                          Parametry produktu ({paramEntries.length})
                        </summary>
                        <div className="mt-2 grid grid-cols-1 gap-1 sm:grid-cols-2">
                          {paramEntries.map(([key, val]) => (
                            <div key={key} className="flex items-baseline gap-2 rounded bg-[#121212] px-3 py-1.5 text-xs">
                              <span className="text-gray-500 shrink-0">{key}</span>
                              <span className="text-white truncate">{val}</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </>
                )
              })()}
            </CardContent>
          </Card>

          {/* Issues list */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Znalezione problemy ({result.issues.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {result.issues.length === 0 ? (
                <div className="p-6 text-center">
                  <CheckCircle className="mx-auto h-8 w-8 text-green-400 mb-2" />
                  <p className="text-sm text-gray-400">Brak problemów — karta produktu jest zgodna!</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {result.issues.map((issue, idx) => (
                    <IssueRow key={idx} issue={issue} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

function IssueRow({ issue }: { issue: AuditIssue }) {
  const severityIcon = {
    error: <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" />,
    info: <CheckCircle className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />,
  }

  return (
    <div className="px-4 py-3 space-y-2">
      <div className="flex items-start gap-3">
        {severityIcon[issue.severity as keyof typeof severityIcon] || severityIcon.warning}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-gray-400">{issue.field}</span>
            <Badge
              variant="outline"
              className={cn('text-[10px]', issue.severity === 'error' ? 'border-red-500/30 text-red-400' : 'border-yellow-500/30 text-yellow-400')}
            >
              {issue.severity}
            </Badge>
          </div>
          <p className="mt-0.5 text-sm text-gray-300">{issue.message}</p>

          {/* AI fix suggestion */}
          {issue.fix_suggestion && (
            <div className="mt-2 flex items-start gap-2 rounded-lg bg-green-500/5 border border-green-500/10 px-3 py-2">
              <Lightbulb className="h-3.5 w-3.5 text-green-400 shrink-0 mt-0.5" />
              <p className="text-xs text-green-300">{issue.fix_suggestion}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
