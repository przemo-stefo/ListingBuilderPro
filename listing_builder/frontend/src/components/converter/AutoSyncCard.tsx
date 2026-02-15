// frontend/src/components/converter/AutoSyncCard.tsx
// Purpose: Automatic Allegro monitoring — detect new offers and convert to marketplace templates
// NOT for: Manual conversion or scraping (that's in page.tsx)

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  RefreshCw,
  Play,
  Pause,
  Clock,
  CheckCircle,
  AlertTriangle,
  Download,
  Loader2,
  Zap,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  getAllegroOffers,
  startStoreConvert,
  getStoreJobStatus,
  downloadStoreJob,
} from '@/lib/api/converter'
import type { GPSRData } from '@/lib/types'

const LS_CONFIG_KEY = 'lbp_autosync_config'
const LS_SYNCED_KEY = 'lbp_synced_offers'

interface SyncConfig {
  enabled: boolean
  frequencyHours: number
  lastCheckAt: string | null
  lastCheckResult: { total: number; newCount: number } | null
}

const DEFAULT_CONFIG: SyncConfig = {
  enabled: false,
  frequencyHours: 24,
  lastCheckAt: null,
  lastCheckResult: null,
}

interface Props {
  allegroConnected: boolean
  marketplace: string
  gpsr: GPSRData
  eurRate: number
}

export default function AutoSyncCard({ allegroConnected, marketplace, gpsr, eurRate }: Props) {
  const [config, setConfig] = useState<SyncConfig>(DEFAULT_CONFIG)
  const [newOfferUrls, setNewOfferUrls] = useState<string[]>([])
  const [checking, setChecking] = useState(false)
  const [converting, setConverting] = useState(false)
  const [convertProgress, setConvertProgress] = useState<string | null>(null)
  const [error, setError] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load config from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LS_CONFIG_KEY)
      if (saved) setConfig(JSON.parse(saved))
    } catch {
      // Ignore parse errors
    }
  }, [])

  // Save config to localStorage on change
  const updateConfig = useCallback((updates: Partial<SyncConfig>) => {
    setConfig((prev) => {
      const next = { ...prev, ...updates }
      localStorage.setItem(LS_CONFIG_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  // Load synced offer IDs
  const getSyncedIds = useCallback((): Set<string> => {
    try {
      const saved = localStorage.getItem(LS_SYNCED_KEY)
      return saved ? new Set(JSON.parse(saved)) : new Set()
    } catch {
      return new Set()
    }
  }, [])

  // Save synced offer IDs
  const saveSyncedIds = useCallback((ids: Set<string>) => {
    localStorage.setItem(LS_SYNCED_KEY, JSON.stringify([...ids]))
  }, [])

  // WHY: Extract Allegro offer ID from URL for reliable comparison
  const extractOfferId = (url: string): string => {
    const match = url.match(/\/oferta\/(?:.*-)?(\d{8,14})/)
    return match ? match[1] : url
  }

  // Check for new offers
  const checkNewOffers = useCallback(async () => {
    if (!allegroConnected || checking) return

    setChecking(true)
    setError('')

    try {
      const result = await getAllegroOffers()
      if (result.error) {
        setError(result.error)
        return
      }

      const syncedIds = getSyncedIds()
      const newUrls = result.urls.filter((url) => !syncedIds.has(extractOfferId(url)))

      setNewOfferUrls(newUrls)
      updateConfig({
        lastCheckAt: new Date().toISOString(),
        lastCheckResult: { total: result.total, newCount: newUrls.length },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd sprawdzania ofert')
    } finally {
      setChecking(false)
    }
  }, [allegroConnected, checking, getSyncedIds, updateConfig])

  // Periodic checking when enabled
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (config.enabled && allegroConnected) {
      // WHY: Check on enable, then every frequencyHours
      // Client-side polling — works when page is open
      const ms = config.frequencyHours * 60 * 60 * 1000
      checkNewOffers()
      intervalRef.current = setInterval(checkNewOffers, ms)
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [config.enabled, config.frequencyHours, allegroConnected]) // eslint-disable-line react-hooks/exhaustive-deps

  // Convert all new offers
  const handleConvertNew = useCallback(async () => {
    if (!marketplace || newOfferUrls.length === 0) return

    setConverting(true)
    setConvertProgress('Uruchamiam konwersję...')
    setError('')

    try {
      const result = await startStoreConvert({
        urls: newOfferUrls,
        marketplace,
        gpsr_data: gpsr,
        eur_rate: eurRate,
      })

      // Poll for completion
      const pollJob = async () => {
        const status = await getStoreJobStatus(result.job_id)
        setConvertProgress(`Przetwarzam... ${status.scraped}/${status.total}`)

        if (status.status === 'done') {
          if (status.download_ready) {
            const blob = await downloadStoreJob(result.job_id)
            const ext = marketplace === 'amazon' ? 'tsv' : 'csv'
            const filename = `autosync_${marketplace}_${new Date().toISOString().slice(0, 10)}.${ext}`
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = filename
            a.click()
            URL.revokeObjectURL(url)
          }

          // Mark offers as synced
          const syncedIds = getSyncedIds()
          newOfferUrls.forEach((url) => syncedIds.add(extractOfferId(url)))
          saveSyncedIds(syncedIds)
          setNewOfferUrls([])
          setConvertProgress(null)
          setConverting(false)
          return
        }

        setTimeout(pollJob, 3000)
      }

      pollJob()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd konwersji')
      setConverting(false)
      setConvertProgress(null)
    }
  }, [marketplace, newOfferUrls, gpsr, eurRate, getSyncedIds, saveSyncedIds])

  const toggleSync = () => updateConfig({ enabled: !config.enabled })

  const formatLastCheck = (iso: string | null): string => {
    if (!iso) return 'nigdy'
    const diff = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'przed chwila'
    if (mins < 60) return `${mins} min temu`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} godz. temu`
    return `${Math.floor(hours / 24)} dni temu`
  }

  const frequencies = [
    { value: 6, label: '6h' },
    { value: 12, label: '12h' },
    { value: 24, label: '24h' },
  ]

  // WHY: Don't show sync if Allegro not connected — it can't work
  if (!allegroConnected) {
    return (
      <Card className="border-dashed border-gray-700">
        <CardContent className="flex items-center gap-3 py-6">
          <Zap className="h-5 w-5 text-gray-600" />
          <div>
            <p className="text-sm text-gray-400">Auto-Sync</p>
            <p className="text-xs text-gray-600">
              Połącz konto Allegro, aby włączyć automatyczne monitorowanie nowych ofert
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className={cn('h-5 w-5', config.enabled ? 'text-green-400' : 'text-gray-400')} />
            <div>
              <CardTitle className="text-lg">Auto-Sync</CardTitle>
              <CardDescription>
                Automatyczne monitorowanie nowych ofert Allegro
              </CardDescription>
            </div>
          </div>
          <Badge
            variant="secondary"
            className={cn(
              'text-[10px]',
              config.enabled ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-500'
            )}
          >
            {config.enabled ? 'Aktywny' : 'Wyłączony'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Status row */}
        <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#121212] p-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-gray-500" />
              <span className="text-xs text-gray-400">
                Ostatnie sprawdzenie: {formatLastCheck(config.lastCheckAt)}
              </span>
            </div>
            {config.lastCheckResult && (
              <span className="text-xs text-gray-500">
                {config.lastCheckResult.total} ofert
              </span>
            )}
          </div>
          <Button
            onClick={checkNewOffers}
            disabled={checking}
            variant="outline"
            size="sm"
            className="h-7 text-xs"
          >
            {checking ? (
              <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="mr-1.5 h-3 w-3" />
            )}
            Sprawdź teraz
          </Button>
        </div>

        {/* New offers badge */}
        {newOfferUrls.length > 0 && (
          <div className="flex items-center justify-between rounded-lg border border-green-500/20 bg-green-500/5 p-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-400" />
              <span className="text-sm text-green-400">
                {newOfferUrls.length} nowych ofert do synchronizacji
              </span>
            </div>
            <Button
              onClick={handleConvertNew}
              disabled={converting || !marketplace}
              size="sm"
              className="h-7 text-xs"
            >
              {converting ? (
                <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
              ) : (
                <Download className="mr-1.5 h-3 w-3" />
              )}
              Konwertuj ({newOfferUrls.length})
            </Button>
          </div>
        )}

        {/* Convert progress */}
        {convertProgress && (
          <div className="rounded-lg border border-gray-800 bg-[#121212] p-3">
            <div className="flex items-center gap-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-400" />
              <span className="text-xs text-gray-400">{convertProgress}</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg bg-red-500/5 p-3">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <span className="text-xs text-red-400">{error}</span>
          </div>
        )}

        {/* Controls row */}
        <div className="flex items-center justify-between">
          {/* Frequency selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Sprawdzaj co:</span>
            <div className="flex gap-1">
              {frequencies.map((f) => (
                <button
                  key={f.value}
                  onClick={() => updateConfig({ frequencyHours: f.value })}
                  className={cn(
                    'rounded px-2.5 py-1 text-xs transition-colors',
                    config.frequencyHours === f.value
                      ? 'bg-white/10 text-white'
                      : 'bg-transparent text-gray-500 hover:text-gray-300'
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Toggle */}
          <Button
            onClick={toggleSync}
            variant={config.enabled ? 'outline' : 'default'}
            size="sm"
            className="h-7 text-xs"
          >
            {config.enabled ? (
              <>
                <Pause className="mr-1.5 h-3 w-3" />
                Wyłącz
              </>
            ) : (
              <>
                <Play className="mr-1.5 h-3 w-3" />
                Włącz Auto-Sync
              </>
            )}
          </Button>
        </div>

        {/* Synced count */}
        {getSyncedIds().size > 0 && (
          <p className="text-[10px] text-gray-600">
            {getSyncedIds().size} ofert już zsynchronizowanych
          </p>
        )}

        {/* Info when no marketplace selected */}
        {!marketplace && config.enabled && (
          <p className="text-[10px] text-yellow-500">
            Wybierz marketplace powyżej, aby móc konwertować nowe oferty
          </p>
        )}
      </CardContent>
    </Card>
  )
}
