// frontend/src/app/converter/page.tsx
// Purpose: Allegro→Marketplace converter page — scrape, translate, map, download
// NOT for: API logic (that's in lib/api/converter.ts and hooks/useConverter.ts)

'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import Link from 'next/link'
import {
  ArrowRightLeft,
  ChevronDown,
  ChevronRight,
  Download,
  Eye,
  HelpCircle,
  Loader2,
  AlertTriangle,
  CheckCircle,
  CheckCircle2,
  XCircle,
  Save,
  Search,
  Package,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import { listProducts } from '@/lib/api/products'
import { useMarketplaces, useConvertProducts, useDownloadTemplate } from '@/lib/hooks/useConverter'
import { useSettings, useUpdateSettings } from '@/lib/hooks/useSettings'
import {
  getStoreUrls,
  startStoreConvert,
  getStoreJobStatus,
  downloadStoreJob,
  getOAuthConnections,
  getAllegroOffers,
  getBolOffers,
} from '@/lib/api/converter'
import type {
  ConvertRequest,
  ConvertResponse,
  ConvertedProductResult,
  GPSRData,
  StoreJobStatus,
} from '@/lib/types'
import AutoSyncCard from '@/components/converter/AutoSyncCard'
import { FaqItem } from '@/components/ui/FaqSection'

// WHY: Default GPSR structure with empty strings — user fills only what they need
const DEFAULT_GPSR: GPSRData = {
  manufacturer_contact: '',
  manufacturer_address: '',
  manufacturer_city: '',
  manufacturer_country: '',
  country_of_origin: '',
  safety_attestation: '',
  responsible_person_type: '',
  responsible_person_name: '',
  responsible_person_address: '',
  responsible_person_country: '',
  amazon_browse_node: '',
  amazon_product_type: '',
  ebay_category_id: '',
  kaufland_category: '',
}

export default function ConverterPage() {
  // Form state
  const [urlsText, setUrlsText] = useState('')
  const [marketplace, setMarketplace] = useState('')
  const [eurRate, setEurRate] = useState(0.23)
  const [delay, setDelay] = useState(3.0)
  const [gpsr, setGpsr] = useState<GPSRData>(DEFAULT_GPSR)

  // Collapsible sections
  const [showSettings, setShowSettings] = useState(false)
  const [showGpsr, setShowGpsr] = useState(false)
  const [showFaq, setShowFaq] = useState(false)

  // Store input
  const [storeName, setStoreName] = useState('')
  const [storeLoading, setStoreLoading] = useState(false)
  const [storeError, setStoreError] = useState('')
  const [storeCount, setStoreCount] = useState<number | null>(null)

  // Imported products picker
  const [showImported, setShowImported] = useState(false)
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([])

  // Allegro OAuth connection
  const [allegroConnected, setAllegroConnected] = useState(false)
  const [allegroLoading, setAllegroLoading] = useState(false)

  // BOL.com connection
  const [bolConnected, setBolConnected] = useState(false)
  const [bolLoading, setBolLoading] = useState(false)

  // Async job (for >20 products)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<StoreJobStatus | null>(null)

  // Results
  const [results, setResults] = useState<ConvertResponse | null>(null)
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set())

  // Hooks
  const { data: marketplaces, isLoading: loadingMarketplaces } = useMarketplaces()
  const convertMutation = useConvertProducts()
  const downloadMutation = useDownloadTemplate()
  const { data: settings } = useSettings()
  const updateSettingsMutation = useUpdateSettings()

  // WHY: Only fetch when section is expanded — enabled: showImported prevents wasted API calls
  const { data: importedData, isLoading: importedLoading } = useQuery({
    queryKey: ['products', { source: 'allegro', page_size: 100 }],
    queryFn: () => listProducts({ source: 'allegro', page_size: 100 }),
    enabled: showImported,
    staleTime: 30000,
  })
  // WHY: Only products with source_url can be converted
  const importedProducts = useMemo(
    () => (importedData?.items || []).filter((p) => p.source_url),
    [importedData]
  )

  // WHY: Auto-fill GPSR from saved settings on mount
  const [gpsrLoaded, setGpsrLoaded] = useState(false)

  // Parse URLs from textarea
  const parseUrls = (): string[] =>
    urlsText
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.length > 0)

  const canSubmit = parseUrls().length > 0 && marketplace !== ''

  // Build the request payload
  const buildPayload = (): ConvertRequest => ({
    urls: parseUrls(),
    marketplace,
    gpsr_data: gpsr,
    eur_rate: eurRate,
    delay,
  })

  // ── Check marketplace connections on mount ──
  useEffect(() => {
    getOAuthConnections()
      .then((conns) => {
        const allegro = conns.find((c) => c.marketplace === 'allegro')
        setAllegroConnected(allegro?.status === 'active')
        const bol = conns.find((c) => c.marketplace === 'bol')
        setBolConnected(bol?.status === 'active')
      })
      .catch(() => {})
  }, [])

  // WHY: Auto-fill GPSR from user settings — only once after settings load
  useEffect(() => {
    if (!settings?.gpsr || gpsrLoaded) return
    const saved = settings.gpsr
    const hasData = Object.values(saved).some((v) => v !== '')
    if (hasData) {
      setGpsr(saved)
    } else {
      // WHY: Open GPSR section when empty so user sees they need to fill it
      setShowGpsr(true)
    }
    setGpsrLoaded(true)
  }, [settings, gpsrLoaded])

  // WHY: After OAuth callback redirects to /converter?allegro=connected
  // Also reads ?urls= param for pre-fill from products page
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('allegro') === 'connected') {
      setAllegroConnected(true)
      window.history.replaceState({}, '', '/converter')
    }
    const urlsParam = params.get('urls')
    if (urlsParam) {
      setUrlsText(decodeURIComponent(urlsParam))
      window.history.replaceState({}, '', '/converter')
    }
  }, [])

  const handleFetchBolOffers = useCallback(async () => {
    setBolLoading(true)
    setStoreError('')
    setStoreCount(null)
    try {
      const result = await getBolOffers()
      if (result.error) {
        setStoreError(result.error)
      } else if (result.total === 0) {
        setStoreError('Nie znaleziono ofert na Twoim koncie BOL.com')
      } else {
        setUrlsText(result.urls.join('\n'))
        setStoreCount(result.total)
      }
    } catch (err) {
      setStoreError(err instanceof Error ? err.message : 'Błąd pobierania ofert BOL')
    } finally {
      setBolLoading(false)
    }
  }, [])

  const handleFetchAllegroOffers = useCallback(async () => {
    setAllegroLoading(true)
    setStoreError('')
    setStoreCount(null)
    try {
      const result = await getAllegroOffers()
      if (result.error) {
        setStoreError(result.error)
      } else if (result.total === 0) {
        setStoreError('Nie znaleziono aktywnych ofert na Twoim koncie')
      } else {
        setUrlsText(result.urls.join('\n'))
        setStoreCount(result.total)
      }
    } catch (err) {
      setStoreError(err instanceof Error ? err.message : 'Błąd pobierania ofert')
    } finally {
      setAllegroLoading(false)
    }
  }, [])

  // ── Store fetch handler ──
  const handleFetchStore = useCallback(async () => {
    if (!storeName.trim()) return
    setStoreLoading(true)
    setStoreError('')
    setStoreCount(null)
    try {
      const result = await getStoreUrls(storeName.trim())
      if (result.error) {
        setStoreError(result.error)
      } else if (result.total === 0) {
        setStoreError('Nie znaleziono ofert w tym sklepie')
      } else {
        setUrlsText(result.urls.join('\n'))
        setStoreCount(result.total)
        if (result.capped) {
          setStoreError(`Pobrano pierwsze ~${result.total} ofert (limit 5 stron)`)
        }
      }
    } catch (err) {
      setStoreError(err instanceof Error ? err.message : 'Błąd pobierania sklepu')
    } finally {
      setStoreLoading(false)
    }
  }, [storeName])

  // ── Polling for async job ──
  useEffect(() => {
    if (!jobId) return
    const poll = async () => {
      try {
        const status = await getStoreJobStatus(jobId)
        setJobStatus(status)
        if (status.status === 'done') {
          if (status.download_ready) {
            const blob = await downloadStoreJob(jobId)
            const ext = marketplace === 'amazon' ? 'tsv' : 'csv'
            const filename = `${marketplace}_store_template.${ext}`
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = filename
            a.click()
            URL.revokeObjectURL(url)
          }
          setJobId(null)
        }
      } catch {
        // Polling error — ignore, retry on next tick
      }
    }
    poll()
    const interval = setInterval(poll, 3000)
    return () => clearInterval(interval)
  }, [jobId, marketplace])

  const handlePreview = () => {
    convertMutation.mutate(buildPayload(), {
      onSuccess: (data) => {
        setResults(data)
        setExpandedProducts(new Set())
      },
    })
  }

  // WHY: >20 products would timeout on sync endpoint, use async job instead
  const handleDownload = async () => {
    const urls = parseUrls()
    if (urls.length > 20) {
      try {
        const result = await startStoreConvert({
          urls,
          marketplace,
          gpsr_data: gpsr,
          eur_rate: eurRate,
        })
        setJobId(result.job_id)
        setJobStatus({
          job_id: result.job_id,
          status: 'processing',
          total: result.total,
          scraped: 0,
          converted: 0,
          failed: 0,
          download_ready: false,
        })
      } catch (err) {
        setStoreError(err instanceof Error ? err.message : 'Nie udało się uruchomić konwersji')
      }
    } else {
      downloadMutation.mutate(buildPayload())
    }
  }

  const toggleProduct = (idx: number) => {
    setExpandedProducts((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  // WHY: Helper for updating a single GPSR field without spreading every time
  const updateGpsr = (field: keyof GPSRData, value: string) => {
    setGpsr((prev) => ({ ...prev, [field]: value }))
  }

  const isLoading = convertMutation.isPending || downloadMutation.isPending || jobId !== null

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Konwerter Allegro → Marketplace</h1>
        <p className="text-sm text-gray-400">
          Przenieś produkty z Allegro na Amazon, eBay lub Kaufland w 3 krokach
        </p>
      </div>

      {/* Section 1: Allegro URLs */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="bg-white/10 text-white text-xs px-2 py-0.5">Krok 1</Badge>
            <CardTitle className="text-lg">Produkty z Allegro</CardTitle>
          </div>
          <CardDescription>Połącz konto, wpisz nazwę sklepu lub wklej linki ręcznie</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* WHY: Allegro OAuth moved to /integrations — here just status + link */}
          <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#121212] p-3">
            <div className="flex items-center gap-2">
              {allegroConnected ? (
                <CheckCircle className="h-4 w-4 text-green-400" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-500" />
              )}
              <span className="text-sm text-gray-300">
                {allegroConnected ? 'Konto Allegro połączone' : 'Konto Allegro niepołączone'}
              </span>
            </div>
            <div className="flex gap-2">
              {allegroConnected && (
                <Button
                  onClick={handleFetchAllegroOffers}
                  disabled={allegroLoading}
                  size="sm"
                >
                  {allegroLoading ? (
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-3 w-3" />
                  )}
                  Pobierz moje oferty
                </Button>
              )}
              <Link
                href="/integrations"
                className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-transparent px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 transition-colors"
              >
                {allegroConnected ? 'Zarządzaj' : 'Połącz w Integracje'}
              </Link>
            </div>
          </div>

          {/* WHY: BOL.com uses Client Credentials — connected via Integrations page */}
          <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#121212] p-3">
            <div className="flex items-center gap-2">
              {bolConnected ? (
                <CheckCircle className="h-4 w-4 text-green-400" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-500" />
              )}
              <span className="text-sm text-gray-300">
                {bolConnected ? 'Konto BOL.com połączone' : 'Konto BOL.com niepołączone'}
              </span>
            </div>
            <div className="flex gap-2">
              {bolConnected && (
                <Button
                  onClick={handleFetchBolOffers}
                  disabled={bolLoading}
                  size="sm"
                >
                  {bolLoading ? (
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-3 w-3" />
                  )}
                  Pobierz oferty BOL
                </Button>
              )}
              <Link
                href="/integrations"
                className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-transparent px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 transition-colors"
              >
                {bolConnected ? 'Zarządzaj' : 'Połącz w Integracje'}
              </Link>
            </div>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-800" />
            <span className="text-xs text-gray-500">lub pobierz z innego sklepu</span>
            <div className="h-px flex-1 bg-gray-800" />
          </div>

          {/* Store input */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Nazwa sklepu lub link do sprzedawcy
            </label>
            <div className="flex gap-2">
              <Input
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                placeholder="np. electronics-shop-pl lub https://allegro.pl/uzytkownik/nazwa"
                onKeyDown={(e) => e.key === 'Enter' && handleFetchStore()}
                disabled={storeLoading}
              />
              <Button
                onClick={handleFetchStore}
                disabled={!storeName.trim() || storeLoading}
                variant="outline"
                className="shrink-0"
              >
                {storeLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                Pobierz oferty
              </Button>
            </div>
            {storeCount !== null && !storeError && (
              <p className="mt-1 text-xs text-green-400">
                Znaleziono {storeCount} ofert
              </p>
            )}
            {storeError && (
              <p className="mt-1 text-xs text-yellow-400">{storeError}</p>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-800" />
            <span className="text-xs text-gray-500">lub wybierz z zaimportowanych produktów</span>
            <div className="h-px flex-1 bg-gray-800" />
          </div>

          {/* Imported products picker */}
          <div>
            <button
              onClick={() => setShowImported(!showImported)}
              className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <Package className="h-4 w-4" />
              <span>Wybierz z bazy{importedData ? ` (${importedProducts.length})` : ''}</span>
              {showImported ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>

            {showImported && (
              <div className="mt-3 rounded-lg border border-gray-800 bg-[#121212] p-3 space-y-3">
                {importedLoading ? (
                  <div className="flex items-center gap-2 text-sm text-gray-400 py-4 justify-center">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Ładowanie produktów...
                  </div>
                ) : importedProducts.length === 0 ? (
                  <p className="text-sm text-gray-500 py-4 text-center">
                    Brak zaimportowanych produktów z Allegro
                  </p>
                ) : (
                  <>
                    {/* Select all / deselect buttons */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        onClick={() => setSelectedProductIds(importedProducts.map((p) => p.id))}
                      >
                        Zaznacz wszystkie
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        onClick={() => setSelectedProductIds([])}
                      >
                        Odznacz
                      </Button>
                      <span className="text-xs text-gray-500 ml-auto">
                        {selectedProductIds.length} z {importedProducts.length}
                      </span>
                    </div>

                    {/* Product list */}
                    <div className="max-h-64 overflow-y-auto space-y-1">
                      {importedProducts.map((product) => {
                        const isSelected = selectedProductIds.includes(product.id)
                        const daysAgo = Math.floor(
                          (Date.now() - new Date(product.created_at).getTime()) / 86400000
                        )
                        const timeLabel = daysAgo === 0 ? 'dziś' : daysAgo === 1 ? 'wczoraj' : `${daysAgo} dni`
                        return (
                          <button
                            key={product.id}
                            onClick={() =>
                              setSelectedProductIds((prev) =>
                                prev.includes(product.id)
                                  ? prev.filter((id) => id !== product.id)
                                  : [...prev, product.id]
                              )
                            }
                            className={cn(
                              'flex items-center gap-3 w-full rounded-md px-3 py-2 text-left transition-colors',
                              isSelected ? 'bg-white/5' : 'hover:bg-white/5'
                            )}
                          >
                            <div
                              className={cn(
                                'w-4 h-4 rounded border flex items-center justify-center shrink-0',
                                isSelected ? 'border-white bg-white' : 'border-gray-600'
                              )}
                            >
                              {isSelected && <CheckCircle2 className="h-3 w-3 text-black" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-white truncate">
                                {product.title_original}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                {product.source_url}
                              </p>
                            </div>
                            <span className="text-xs text-gray-600 shrink-0">{timeLabel}</span>
                          </button>
                        )
                      })}
                    </div>

                    {/* Load button */}
                    <Button
                      size="sm"
                      disabled={selectedProductIds.length === 0}
                      className="w-full"
                      onClick={() => {
                        const urls = importedProducts
                          .filter((p) => selectedProductIds.includes(p.id))
                          .map((p) => p.source_url!)
                        setUrlsText(urls.join('\n'))
                        setSelectedProductIds([])
                        setShowImported(false)
                      }}
                    >
                      Wczytaj {selectedProductIds.length > 0 ? `${selectedProductIds.length} produktów` : ''}
                    </Button>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-800" />
            <span className="text-xs text-gray-500">lub wklej linki ręcznie</span>
            <div className="h-px flex-1 bg-gray-800" />
          </div>

          {/* Manual URL textarea */}
          <textarea
            value={urlsText}
            onChange={(e) => setUrlsText(e.target.value)}
            placeholder="https://allegro.pl/oferta/example-product-123456789&#10;https://allegro.pl/oferta/another-product-987654321"
            rows={5}
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
          />
          <p className="mt-1 text-xs text-gray-500">
            {parseUrls().length > 0
              ? `Znaleziono ${parseUrls().length} ${parseUrls().length === 1 ? 'produkt' : parseUrls().length < 5 ? 'produkty' : 'produktów'} (max 500)`
              : 'Wklej linki do produktów Allegro, po jednym w linii'}
          </p>
        </CardContent>
      </Card>

      {/* Section 2: Target Marketplace */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="bg-white/10 text-white text-xs px-2 py-0.5">Krok 2</Badge>
            <CardTitle className="text-lg">Gdzie wystawić?</CardTitle>
          </div>
          <CardDescription>Wybierz marketplace, na który chcesz przenieść produkty</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingMarketplaces ? (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Ładowanie...
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {marketplaces?.map((mp) => (
                <button
                  key={mp.id}
                  onClick={() => setMarketplace(mp.id)}
                  className={cn(
                    'rounded-lg border p-4 text-left transition-colors',
                    marketplace === mp.id
                      ? 'border-white bg-white/5'
                      : 'border-gray-800 bg-[#1A1A1A] hover:border-gray-600'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-white">{mp.name}</span>
                    <Badge variant="secondary" className="text-[10px]">
                      {mp.extension}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">{mp.format}</p>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Settings (collapsible) */}
      <Card>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="flex w-full items-center justify-between p-6"
        >
          <div>
            <h3 className="text-lg font-semibold text-white">Ustawienia</h3>
            <p className="text-sm text-gray-400">Kurs wymiany PLN → EUR i prędkość pobierania</p>
          </div>
          {showSettings ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {showSettings && (
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Kurs EUR (PLN → EUR)
              </label>
              <Input
                type="number"
                step="0.01"
                value={eurRate}
                onChange={(e) => setEurRate(parseFloat(e.target.value) || 0.23)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Opóźnienie między produktami (sekundy)
              </label>
              <Input
                type="number"
                step="0.5"
                min="1"
                value={delay}
                onChange={(e) => setDelay(parseFloat(e.target.value) || 3.0)}
              />
            </div>
          </CardContent>
        )}
      </Card>

      {/* Section 4: GPSR Data (collapsible) */}
      <Card>
        <div className="flex items-center justify-between p-6">
          <button
            onClick={() => setShowGpsr(!showGpsr)}
            className="flex flex-1 items-center justify-between"
          >
            <div>
              <h3 className="text-lg font-semibold text-white">Dane producenta (opcjonalne)</h3>
              <p className="text-sm text-gray-400">GPSR, osoba odpowiedzialna w UE i kategorie — wypełnij raz dla wszystkich produktów</p>
            </div>
            {showGpsr ? (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
          </button>
          {/* WHY: Save GPSR to settings so it auto-fills next time */}
          {showGpsr && (
            <Button
              size="sm"
              variant="outline"
              className="ml-3 shrink-0"
              disabled={updateSettingsMutation.isPending}
              onClick={(e) => {
                e.stopPropagation()
                updateSettingsMutation.mutate({ gpsr: gpsr as GPSRData })
              }}
            >
              {updateSettingsMutation.isPending ? (
                <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
              ) : (
                <Save className="mr-1.5 h-3 w-3" />
              )}
              Zapisz domyślne
            </Button>
          )}
        </div>
        {showGpsr && (
          <CardContent className="space-y-6">
            {/* Manufacturer */}
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-300">Producent</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kontakt</label>
                  <Input
                    value={gpsr.manufacturer_contact}
                    onChange={(e) => updateGpsr('manufacturer_contact', e.target.value)}
                    placeholder="Nazwa producenta"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Adres</label>
                  <Input
                    value={gpsr.manufacturer_address}
                    onChange={(e) => updateGpsr('manufacturer_address', e.target.value)}
                    placeholder="Ulica i numer"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Miasto</label>
                  <Input
                    value={gpsr.manufacturer_city}
                    onChange={(e) => updateGpsr('manufacturer_city', e.target.value)}
                    placeholder="Miasto"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kraj</label>
                  <Input
                    value={gpsr.manufacturer_country}
                    onChange={(e) => updateGpsr('manufacturer_country', e.target.value)}
                    placeholder="PL, DE, CN..."
                  />
                </div>
              </div>
            </div>

            {/* Origin & Safety */}
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-300">Pochodzenie i bezpieczeństwo</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kraj pochodzenia</label>
                  <Input
                    value={gpsr.country_of_origin}
                    onChange={(e) => updateGpsr('country_of_origin', e.target.value)}
                    placeholder="CN, PL, DE..."
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Atest bezpieczeństwa</label>
                  <Input
                    value={gpsr.safety_attestation}
                    onChange={(e) => updateGpsr('safety_attestation', e.target.value)}
                    placeholder="CE, GS..."
                  />
                </div>
              </div>
            </div>

            {/* Responsible Person */}
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-300">Osoba odpowiedzialna (UE)</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Typ</label>
                  <Input
                    value={gpsr.responsible_person_type}
                    onChange={(e) => updateGpsr('responsible_person_type', e.target.value)}
                    placeholder="Producent / Importer"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Nazwa</label>
                  <Input
                    value={gpsr.responsible_person_name}
                    onChange={(e) => updateGpsr('responsible_person_name', e.target.value)}
                    placeholder="Nazwa firmy"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Adres</label>
                  <Input
                    value={gpsr.responsible_person_address}
                    onChange={(e) => updateGpsr('responsible_person_address', e.target.value)}
                    placeholder="Pełny adres"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kraj</label>
                  <Input
                    value={gpsr.responsible_person_country}
                    onChange={(e) => updateGpsr('responsible_person_country', e.target.value)}
                    placeholder="DE, PL..."
                  />
                </div>
              </div>
            </div>

            {/* Category IDs */}
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-300">ID kategorii</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Amazon Browse Node</label>
                  <Input
                    value={gpsr.amazon_browse_node}
                    onChange={(e) => updateGpsr('amazon_browse_node', e.target.value)}
                    placeholder="np. 3169011"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Amazon Product Type</label>
                  <Input
                    value={gpsr.amazon_product_type}
                    onChange={(e) => updateGpsr('amazon_product_type', e.target.value)}
                    placeholder="np. HOME"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">eBay Category ID</label>
                  <Input
                    value={gpsr.ebay_category_id}
                    onChange={(e) => updateGpsr('ebay_category_id', e.target.value)}
                    placeholder="np. 11700"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kaufland Category</label>
                  <Input
                    value={gpsr.kaufland_category}
                    onChange={(e) => updateGpsr('kaufland_category', e.target.value)}
                    placeholder="np. Haushalt"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Section 5: Auto-Sync */}
      <AutoSyncCard
        allegroConnected={allegroConnected}
        marketplace={marketplace}
        gpsr={gpsr}
        eurRate={eurRate}
      />

      {/* Section 6: FAQ */}
      <Card>
        <button
          onClick={() => setShowFaq(!showFaq)}
          className="flex w-full items-center justify-between p-6"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5 text-gray-400" />
            <div>
              <h3 className="text-lg font-semibold text-white">FAQ — Jak korzystać</h3>
              <p className="text-sm text-gray-400">Instrukcja krok po kroku</p>
            </div>
          </div>
          {showFaq ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {showFaq && (
          <CardContent className="space-y-4 pt-0">
            <FaqItem
              question="Jak pobrać oferty ze sklepu Allegro?"
              answer="Masz 3 opcje: (1) Połącz swoje konto Allegro — kliknij 'Połącz z Allegro', zaloguj się i kliknij 'Pobierz moje oferty (API)'. To najszybsza i darmowa metoda. (2) Wpisz nazwę sklepu w pole 'Sklep Allegro' i kliknij 'Pobierz oferty'. System zescrapuje stronę sklepu. (3) Wklej URLe ręcznie do pola tekstowego, po jednym w linii."
            />
            <FaqItem
              question="Co to jest 'Połącz z Allegro'?"
              answer="Logowanie przez OAuth — jak 'Zaloguj przez Google'. Klikasz, logujesz się na swoje konto Allegro, zezwalasz na dostęp i wracasz do convertera. System pobierze Twoje oferty przez oficjalne API Allegro — za darmo, bez scrapowania."
            />
            <FaqItem
              question="Co to jest 'Target Marketplace'?"
              answer="Wybierz gdzie chcesz wystawić produkty: Amazon.de (plik TSV), eBay.de (plik CSV) lub Kaufland.de (plik CSV). Każdy marketplace ma inny format pliku do importu."
            />
            <FaqItem
              question="Co to jest GPSR?"
              answer="General Product Safety Regulation — wymóg UE od 2024. Musisz podać dane producenta, osoby odpowiedzialnej w UE i kraj pochodzenia. Wypełnij raz — dane dotyczą wszystkich produktów tego sprzedawcy. Bez tego Amazon/eBay mogą odrzucić listing."
            />
            <FaqItem
              question="Co to jest 'EUR exchange rate'?"
              answer="Kurs wymiany PLN → EUR. Domyślnie 0.23 (1 PLN ≈ 0.23 EUR). Zmień go na aktualny kurs przed konwersją, żeby ceny były poprawne."
            />
            <FaqItem
              question="Co to jest 'Amazon Browse Node' i 'Product Type'?"
              answer="Browse Node to ID kategorii na Amazon (np. 3169011 = Kawa). Product Type to typ produktu (np. HOME, BEAUTY). Znajdziesz je w Amazon Seller Central → Add a Product → wybierz kategorię."
            />
            <FaqItem
              question="Czym się różni 'Preview' od 'Download Template'?"
              answer="Preview pokazuje skonwertowane dane na ekranie — możesz sprawdzić tłumaczenia, ceny, pola przed pobraniem. Download Template generuje gotowy plik TSV/CSV do uploadu na marketplace."
            />
            <FaqItem
              question="Co oznacza progress bar 'Przetwarzam 12/47'?"
              answer="Przy >20 produktach konwersja działa w tle. Każdy produkt jest osobno scrapowany, tłumaczony na niemiecki przez AI i mapowany na pola marketplace. Progress bar pokazuje ile produktów już przetworzono. Plik pobierze się automatycznie po zakończeniu."
            />
            <FaqItem
              question="Co jeśli niektóre produkty mają błędy?"
              answer="Produkty z błędami (np. Allegro zablokował scraping) są pomijane. Reszta konwertuje się normalnie. W podsumowaniu zobaczysz ile się udało, ile nie, i jakie warnings dostałeś (np. brakujący EAN)."
            />
            <FaqItem
              question="Co to jest Auto-Sync?"
              answer="Automatyczne monitorowanie Twojego konta Allegro. Gdy włączone, system co 6/12/24 godzin sprawdza czy masz nowe oferty na Allegro. Jeśli znajdzie nowe produkty — pokazuje badge z liczbą nowych ofert. Kliknij 'Konwertuj' i system automatycznie przetłumaczy je na wybrany marketplace i pobierze gotowy plik. Wymaga połączenia z Allegro (OAuth)."
            />
            <FaqItem
              question="Jak wgrać plik na Amazon?"
              answer="Amazon Seller Central → Catalog → Add Products via Upload → Download Template (żeby sprawdzić format) → Upload your file (wgraj pobrany TSV). Upewnij się, że wybrałeś właściwy Product Type i Browse Node."
            />
          </CardContent>
        )}
      </Card>

      {/* Action Bar */}
      <Card className={cn(!canSubmit && 'opacity-60')}>
        <CardContent className="flex items-center gap-3 py-4">
          <Badge variant="secondary" className="bg-white/10 text-white text-xs px-2 py-0.5 shrink-0">Krok 3</Badge>
          <Button
            onClick={handlePreview}
            disabled={!canSubmit || isLoading}
            variant="outline"
          >
            {convertMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Eye className="mr-2 h-4 w-4" />
            )}
            Podgląd danych
          </Button>
          <Button
            onClick={handleDownload}
            disabled={!canSubmit || isLoading}
          >
            {downloadMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            Pobierz plik do importu
          </Button>
          {isLoading && !jobId && (
            <span className="text-xs text-gray-500">
              Tłumaczenie i konwersja — to może chwilę potrwać...
            </span>
          )}
        </CardContent>
      </Card>

      {/* Progress bar for async store conversion */}
      {jobStatus && jobId && (
        <Card>
          <CardContent className="py-4 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">
                Przetwarzam produkt {jobStatus.scraped} z {jobStatus.total}...
              </span>
              <span className="text-gray-500">
                {jobStatus.converted} gotowych
                {jobStatus.failed > 0 && `, ${jobStatus.failed} nie udało się`}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-800">
              <div
                className="h-2 rounded-full bg-white transition-all duration-500"
                style={{
                  width: `${jobStatus.total > 0 ? (jobStatus.scraped / jobStatus.total) * 100 : 0}%`,
                }}
              />
            </div>
            {jobStatus.status === 'done' && (
              <p className="text-xs text-green-400">
                Gotowe! Plik pobiera się automatycznie.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Section 5: Results */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Wyniki</CardTitle>
            <CardDescription>
              Skonwertowano {results.succeeded} z {results.total} produktów dla{' '}
              {results.marketplace}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary badges */}
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-1 rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400">
                <CheckCircle className="h-3 w-3" />
                {results.succeeded} udanych
              </div>
              {results.failed > 0 && (
                <div className="flex items-center gap-1 rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-400">
                  <XCircle className="h-3 w-3" />
                  {results.failed} błędów
                </div>
              )}
              {results.warnings.length > 0 && (
                <div className="flex items-center gap-1 rounded-full bg-yellow-500/10 px-3 py-1 text-xs text-yellow-400">
                  <AlertTriangle className="h-3 w-3" />
                  {results.warnings.length} ostrzeżeń
                </div>
              )}
            </div>

            {/* Product cards */}
            <div className="space-y-2">
              {results.products.map((product, idx) => (
                <ProductResultCard
                  key={idx}
                  product={product}
                  index={idx}
                  expanded={expandedProducts.has(idx)}
                  onToggle={() => toggleProduct(idx)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// WHY: FaqItem now imported from shared @/components/ui/FaqSection


// WHY: Separate component to keep the main page cleaner and avoid re-rendering everything
function ProductResultCard({
  product,
  index,
  expanded,
  onToggle,
}: {
  product: ConvertedProductResult
  index: number
  expanded: boolean
  onToggle: () => void
}) {
  const hasError = product.error !== null
  const hasWarnings = product.warnings.length > 0

  return (
    <div className="rounded-lg border border-gray-800 bg-[#1A1A1A]">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-4"
      >
        <div className="flex items-center gap-3">
          {hasError ? (
            <XCircle className="h-4 w-4 text-red-400" />
          ) : hasWarnings ? (
            <AlertTriangle className="h-4 w-4 text-yellow-400" />
          ) : (
            <CheckCircle className="h-4 w-4 text-green-400" />
          )}
          <div className="text-left">
            <p className="text-sm text-white">
              Produkt {index + 1}
              {product.source_id && (
                <span className="ml-2 text-xs text-gray-500">({product.source_id})</span>
              )}
            </p>
            <p className="text-xs text-gray-500 truncate max-w-md">
              {product.source_url}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasWarnings && (
            <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-400 text-[10px]">
              {product.warnings.length} ostrzeżeń
            </Badge>
          )}
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-800 p-4 space-y-3">
          {/* Error message */}
          {hasError && (
            <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">
              {product.error}
            </div>
          )}

          {/* Warnings */}
          {hasWarnings && (
            <div className="space-y-1">
              {product.warnings.map((w, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded bg-yellow-500/5 px-3 py-2 text-xs text-yellow-400"
                >
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                  {w}
                </div>
              ))}
            </div>
          )}

          {/* Mapped fields table */}
          {Object.keys(product.fields).length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Pole</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Wartość</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(product.fields).map(([key, val]) => (
                    <tr key={key} className="border-b border-gray-800/50">
                      <td className="py-1.5 pr-4 font-mono text-gray-400">{key}</td>
                      <td className="py-1.5 text-white break-all">{val || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
