// frontend/src/app/optimize/components/ListingCard.tsx
// Purpose: Generated listing display with copy/export buttons and Allegro publish
// NOT for: Scores, keyword intel, or feedback (those are separate components)

'use client'

import { useState } from 'react'
import { Download, Copy, Check, XCircle, AlertTriangle, Lock, Upload, FileText, Braces, Table, Share2, Loader2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTier } from '@/lib/hooks/useTier'
import AllegroUpdateDialog from './AllegroUpdateDialog'
import { downloadCSV, downloadEbayCsv, downloadJSON, downloadExcel, CopyButton, ListingSection } from './ResultDisplay'
import { downloadPDF } from '@/lib/utils/pdfExport'
import { createShareLink } from '@/lib/api/optimizerHistory'
import type { OptimizerResponse } from '@/lib/types'

export function ListingCard({
  listing, compliance, copiedField, onCopy, fullResponse, isAllegroConnected,
}: {
  listing: OptimizerResponse['listing']
  compliance: OptimizerResponse['compliance']
  copiedField: string | null
  onCopy: (text: string, field: string) => void
  fullResponse?: OptimizerResponse
  isAllegroConnected?: boolean
}) {
  const { isPremium } = useTier()
  const [showAllegroDialog, setShowAllegroDialog] = useState(false)
  const [sharing, setSharing] = useState(false)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [shareError, setShareError] = useState(false)

  const handleShare = async () => {
    if (!fullResponse || sharing) return
    setSharing(true)
    setShareError(false)
    try {
      const token = await createShareLink({
        listing: fullResponse.listing,
        scores: fullResponse.scores,
        compliance: fullResponse.compliance,
        product_title: fullResponse.listing.title.slice(0, 100),
        brand: fullResponse.brand,
        marketplace: fullResponse.marketplace,
      })
      const url = `${window.location.origin}/share/${token}`
      setShareUrl(url)
      navigator.clipboard.writeText(url)
    } catch {
      setShareError(true)
      setTimeout(() => setShareError(false), 3000)
    } finally {
      setSharing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Wygenerowany listing</CardTitle>
          <div className="flex items-center gap-2">
            {fullResponse && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && downloadCSV(fullResponse)}
                disabled={!isPremium}
                title={!isPremium ? 'CSV Export dostepny w Premium' : undefined}
              >
                <Download className="mr-1 h-3 w-3" />
                CSV
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            {fullResponse && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && downloadPDF(fullResponse)}
                disabled={!isPremium}
                title={!isPremium ? 'PDF Export dostepny w Premium' : undefined}
              >
                <FileText className="mr-1 h-3 w-3" />
                PDF
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            {fullResponse && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && downloadEbayCsv(fullResponse)}
                disabled={!isPremium}
                title={!isPremium ? 'eBay CSV dostepny w Premium' : undefined}
              >
                <Download className="mr-1 h-3 w-3" />
                eBay CSV
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            {fullResponse && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && downloadJSON(fullResponse)}
                disabled={!isPremium}
                title={!isPremium ? 'JSON Export dostepny w Premium' : undefined}
              >
                <Braces className="mr-1 h-3 w-3" />
                JSON
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            {fullResponse && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && downloadExcel(fullResponse)}
                disabled={!isPremium}
                title={!isPremium ? 'Excel Export dostepny w Premium' : undefined}
              >
                <Table className="mr-1 h-3 w-3" />
                Excel
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            {isAllegroConnected && (
              <Button
                variant="outline" size="sm"
                onClick={() => isPremium && setShowAllegroDialog(true)}
                disabled={!isPremium}
                title={!isPremium ? 'Allegro Update dostepny w Premium' : undefined}
              >
                <Upload className="mr-1 h-3 w-3" />
                Allegro
                {!isPremium && <Lock className="ml-1 h-2.5 w-2.5 text-amber-400" />}
              </Button>
            )}
            <Button
              variant="outline" size="sm"
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
              {copiedField === 'all' ? <Check className="mr-1 h-3 w-3" /> : <Copy className="mr-1 h-3 w-3" />}
              Kopiuj wszystko
            </Button>
            {fullResponse && isPremium && (
              <Button
                variant="outline" size="sm"
                disabled={sharing}
                onClick={handleShare}
              >
                {sharing ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : shareError ? (
                  <XCircle className="mr-1 h-3 w-3 text-red-400" />
                ) : shareUrl ? (
                  <Check className="mr-1 h-3 w-3 text-green-400" />
                ) : (
                  <Share2 className="mr-1 h-3 w-3" />
                )}
                {shareError ? 'Blad' : shareUrl ? 'Skopiowano link' : 'Udostepnij'}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <ListingSection
          label="Tytul" content={listing.title} charCount={listing.title.length}
          maxChars={200} field="title" copiedField={copiedField} onCopy={onCopy}
        />
        {/* Bullet Points */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-300">Punkty (Bullet Points)</h3>
              <span className="text-xs text-gray-500">{listing.bullet_points.length} punktow</span>
            </div>
            <CopyButton text={listing.bullet_points.join('\n')} field="bullets" copiedField={copiedField} onCopy={onCopy} />
          </div>
          <div className="space-y-2">
            {listing.bullet_points.map((bullet, i) => (
              <div key={i} className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white">
                {bullet}
              </div>
            ))}
          </div>
        </div>
        <ListingSection
          label="Opis" content={listing.description} charCount={listing.description.length}
          maxChars={2000} field="description" copiedField={copiedField} onCopy={onCopy} isHtml
        />
        <ListingSection
          label="Slowa kluczowe backend" content={listing.backend_keywords}
          charCount={new TextEncoder().encode(listing.backend_keywords).length}
          maxChars={249} unitLabel="bajtow" field="backend" copiedField={copiedField} onCopy={onCopy} mono
        />
        {(compliance.errors.length > 0 || compliance.warnings.length > 0) && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Uwagi zgodnosci</h3>
            {compliance.errors.map((err, i) => (
              <div key={`e-${i}`} className="flex items-start gap-2 rounded bg-red-500/10 px-3 py-2 text-xs text-red-400">
                <XCircle className="mt-0.5 h-3 w-3 shrink-0" />{err}
              </div>
            ))}
            {compliance.warnings.map((warn, i) => (
              <div key={`w-${i}`} className="flex items-start gap-2 rounded bg-yellow-500/10 px-3 py-2 text-xs text-yellow-400">
                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />{warn}
              </div>
            ))}
          </div>
        )}
      </CardContent>
      {isAllegroConnected && (
        <AllegroUpdateDialog
          open={showAllegroDialog} onClose={() => setShowAllegroDialog(false)}
          title={listing.title} descriptionHtml={listing.description}
        />
      )}
    </Card>
  )
}
