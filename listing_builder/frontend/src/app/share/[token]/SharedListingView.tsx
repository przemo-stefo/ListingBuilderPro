// frontend/src/app/share/[token]/SharedListingView.tsx
// Purpose: Client component for rendering shared listing data
// NOT for: Auth or editing

'use client'

import { useState, useEffect } from 'react'
import DOMPurify from 'dompurify'
import { Loader2, ExternalLink } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn, SAFE_HTML_TAGS } from '@/lib/utils'

interface SharedData {
  product_title: string
  brand: string
  marketplace: string
  listing: {
    title: string
    bullet_points: string[]
    description: string
    backend_keywords: string
  }
  scores?: {
    coverage_pct: number
    compliance_status: string
    backend_utilization_pct: number
    backend_byte_size: number
  }
  compliance?: {
    errors: string[]
    warnings: string[]
  }
  created_at?: string
}

export default function SharedListingView({ token }: { token: string }) {
  const [data, setData] = useState<SharedData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchShare = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || ''
        const res = await fetch(`${backendUrl}/api/proxy/optimizer/share/${token}`)
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `HTTP ${res.status}`)
        }
        setData(await res.json())
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Nie udalo sie zaladowac listingu')
      } finally {
        setLoading(false)
      }
    }
    fetchShare()
  }, [token])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#121212]">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#121212]">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <p className="text-lg text-red-400">{error}</p>
            <p className="mt-2 text-sm text-gray-500">Ten link moze byc nieprawidlowy lub wygasl.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!data) return null

  const { listing, scores } = data

  return (
    <div className="min-h-screen bg-[#121212] py-8">
      <div className="mx-auto max-w-3xl space-y-6 px-4">
        {/* Header */}
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Udostepniony listing z OctoHelper</p>
          <h1 className="text-xl font-bold text-white">{data.product_title}</h1>
          <div className="mt-2 flex items-center justify-center gap-2">
            <Badge variant="secondary" className="text-xs">{data.marketplace}</Badge>
            <Badge variant="secondary" className="text-xs">{data.brand}</Badge>
            {data.created_at && (
              <span className="text-xs text-gray-500">
                {new Date(data.created_at).toLocaleDateString('pl-PL')}
              </span>
            )}
          </div>
        </div>

        {/* Scores */}
        {scores && (
          <div className="flex flex-wrap justify-center gap-3">
            <ScorePill
              label="Pokrycie"
              value={`${scores.coverage_pct}%`}
              color={scores.coverage_pct >= 96 ? 'green' : scores.coverage_pct >= 82 ? 'yellow' : 'red'}
            />
            <ScorePill
              label="Zgodnosc"
              value={scores.compliance_status}
              color={scores.compliance_status === 'PASS' ? 'green' : scores.compliance_status === 'WARNING' ? 'yellow' : 'red'}
            />
            <ScorePill
              label="Backend"
              value={`${scores.backend_utilization_pct}%`}
              color={scores.backend_utilization_pct >= 80 ? 'green' : 'yellow'}
            />
          </div>
        )}

        {/* Title */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-400">Tytul</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-white">{listing.title}</p>
            <span className="text-xs text-gray-500">{listing.title.length}/200 zn</span>
          </CardContent>
        </Card>

        {/* Bullets */}
        {listing.bullet_points.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm text-gray-400">Bullet Points ({listing.bullet_points.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {listing.bullet_points.map((b, i) => (
                <div key={i} className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white">
                  {b}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-400">Opis</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="listing-html rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-5 [&_b]:font-semibold"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(listing.description, { ALLOWED_TAGS: SAFE_HTML_TAGS }) }}
            />
          </CardContent>
        </Card>

        {/* Backend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-400">Backend Keywords</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 font-mono text-xs text-white">
              {listing.backend_keywords}
            </div>
            <span className="text-xs text-gray-500">
              {new TextEncoder().encode(listing.backend_keywords).length}/249 B
            </span>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <a
            href="https://panel.octohelper.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
          >
            Wygenerowano z OctoHelper Optimizer
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  )
}

function ScorePill({ label, value, color }: { label: string; value: string; color: 'green' | 'yellow' | 'red' }) {
  const colors = {
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
    yellow: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
  }
  return (
    <div className={cn('rounded-lg border px-3 py-1.5 text-xs', colors[color])}>
      <span className="text-gray-500">{label}: </span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
