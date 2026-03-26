// frontend/src/app/catalog-health/components/ScanTab.tsx
// Purpose: Start scan + monitor progress + scan history
// NOT for: Issue display (that's IssuesTab)

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useStartScan, useScanStatus, useScanHistory, useCatalogHealthStatus } from '@/lib/hooks/useCatalogHealth'
import { Play, Loader2, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'

const MARKETPLACES = [
  { code: 'DE', label: 'Amazon.de (Niemcy)' },
  { code: 'FR', label: 'Amazon.fr (Francja)' },
  { code: 'IT', label: 'Amazon.it (Wlochy)' },
  { code: 'ES', label: 'Amazon.es (Hiszpania)' },
  { code: 'PL', label: 'Amazon.pl (Polska)' },
  { code: 'NL', label: 'Amazon.nl (Holandia)' },
  { code: 'SE', label: 'Amazon.se (Szwecja)' },
  { code: 'BE', label: 'Amazon.com.be (Belgia)' },
]

const STATUS_CONFIG: Record<string, { icon: typeof Clock; color: string; label: string }> = {
  pending: { icon: Clock, color: 'text-amber-400', label: 'Oczekuje' },
  scanning: { icon: Loader2, color: 'text-blue-400', label: 'Skanowanie' },
  completed: { icon: CheckCircle, color: 'text-green-400', label: 'Zakonczone' },
  failed: { icon: XCircle, color: 'text-red-400', label: 'Blad' },
}

interface ScanTabProps {
  onViewIssues: (scanId: string) => void
}

export default function ScanTab({ onViewIssues }: ScanTabProps) {
  const [marketplace, setMarketplace] = useState('DE')
  const [activeScanId, setActiveScanId] = useState<string | null>(null)

  const { data: status } = useCatalogHealthStatus()
  const startScan = useStartScan()
  const { data: activeScan } = useScanStatus(activeScanId)
  const { data: history, isLoading: historyLoading } = useScanHistory()

  const handleStartScan = async () => {
    const scan = await startScan.mutateAsync(marketplace)
    setActiveScanId(scan.id)
  }

  const credentialsOk = status?.credentials_configured && status?.has_refresh_token
  const isScanning = activeScan?.status === 'pending' || activeScan?.status === 'scanning'

  return (
    <div className="space-y-6">
      {/* SP-API credentials warning */}
      {status && !credentialsOk && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-900 bg-amber-950/30 p-4">
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-400" />
          <div className="text-sm text-amber-300">
            {!status.credentials_configured
              ? 'Amazon SP-API nie jest skonfigurowane. Skontaktuj sie z administratorem.'
              : (
                <>
                  Aby uruchomic skan, najpierw polacz konto Amazon.{' '}
                  <Link href="/integrations" className="font-medium underline hover:text-amber-200">
                    Przejdz do Integracji &rarr;
                  </Link>
                </>
              )}
          </div>
        </div>
      )}

      {/* Start scan */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-6">
        <h3 className="mb-4 text-lg font-medium text-white">Nowy skan katalogowy</h3>
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="mb-1.5 block text-sm text-gray-400">Marketplace</label>
            <select
              value={marketplace}
              onChange={(e) => setMarketplace(e.target.value)}
              className="w-full rounded-md border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white focus:border-gray-500 focus:outline-none"
            >
              {MARKETPLACES.map((m) => (
                <option key={m.code} value={m.code}>{m.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleStartScan}
            disabled={!credentialsOk || startScan.isPending || isScanning}
            className="flex items-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {startScan.isPending || isScanning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isScanning ? 'Skanowanie...' : 'Rozpocznij skan'}
          </button>
        </div>
      </div>

      {/* Active scan progress */}
      {activeScan && isScanning && (
        <div className="rounded-lg border border-blue-900 bg-blue-950/20 p-5">
          <div className="mb-3 flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
            <span className="text-sm font-medium text-blue-300">
              Skan w toku — {activeScan.progress?.phase || 'inicjalizacja'}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-500"
              style={{ width: `${activeScan.progress?.percent || 0}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {activeScan.total_listings > 0 && `${activeScan.total_listings} listingow`}
            {activeScan.issues_found > 0 && ` · ${activeScan.issues_found} problemow znalezionych`}
          </p>
        </div>
      )}

      {/* Completed scan result */}
      {activeScan && activeScan.status === 'completed' && (
        <div className="rounded-lg border border-green-900 bg-green-950/20 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-400" />
              <span className="text-sm font-medium text-green-300">Skan zakonczony</span>
            </div>
            <button
              onClick={() => onViewIssues(activeScan.id)}
              className="rounded-md bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
            >
              Zobacz {activeScan.issues_found} problemow
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {activeScan.total_listings} listingow · {activeScan.issues_found} problemow · {activeScan.marketplace}
          </p>
        </div>
      )}

      {/* Failed scan */}
      {activeScan && activeScan.status === 'failed' && (
        <div className="rounded-lg border border-red-900 bg-red-950/20 p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-400" />
            <span className="text-sm text-red-300">{activeScan.error_message || 'Skan zakonczyl sie bledem'}</span>
          </div>
        </div>
      )}

      {/* Scan history */}
      <div className="rounded-lg border border-gray-800 bg-[#1A1A1A] p-5">
        <h3 className="mb-4 text-sm font-medium text-gray-300">Historia skanow</h3>
        {historyLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded border border-gray-800 bg-[#121212]" />
            ))}
          </div>
        ) : !history?.scans.length ? (
          <p className="text-sm text-gray-500">Brak skanow — uruchom pierwszy skan powyzej</p>
        ) : (
          <div className="space-y-2">
            {history.scans.map((scan) => {
              const cfg = STATUS_CONFIG[scan.status] || STATUS_CONFIG.pending
              const StatusIcon = cfg.icon
              return (
                <div
                  key={scan.id}
                  className="flex items-center justify-between rounded-md border border-gray-800 bg-[#121212] px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <StatusIcon className={`h-4 w-4 ${cfg.color} ${scan.status === 'scanning' ? 'animate-spin' : ''}`} />
                    <div>
                      <p className="text-sm text-white">{scan.marketplace}</p>
                      <p className="text-xs text-gray-500">
                        {scan.created_at ? new Date(scan.created_at).toLocaleString('pl-PL') : '—'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">
                      {scan.total_listings} listingow · {scan.issues_found} problemow
                    </span>
                    {scan.status === 'completed' && scan.issues_found > 0 && (
                      <button
                        onClick={() => onViewIssues(scan.id)}
                        className="rounded bg-white/5 px-2.5 py-1 text-xs text-gray-300 hover:bg-white/10"
                      >
                        Problemy
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
