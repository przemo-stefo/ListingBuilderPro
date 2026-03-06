// frontend/src/app/converter/page.tsx
// Purpose: Allegro→Marketplace converter — wizard flow with 4 steps
// NOT for: API logic (that's in lib/api/converter.ts and hooks/useConverter.ts)

'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
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
  Package,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import { listProducts } from '@/lib/api/products'
import { useMarketplaces, useDownloadTemplate } from '@/lib/hooks/useConverter'
import { apiRequest } from '@/lib/api/client'
import { useSettings, useUpdateSettings } from '@/lib/hooks/useSettings'
import { useToast } from '@/lib/hooks/useToast'
import type { ConvertResponse, ConvertedProductResult, GPSRData } from '@/lib/types'
import { FaqItem } from '@/components/ui/FaqSection'
import { ConverterStepper } from './components/ConverterStepper'

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
  // Wizard state
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())

  // Form state
  const [marketplace, setMarketplace] = useState('')
  const [eurRate, setEurRate] = useState(0.23)
  const [gpsr, setGpsr] = useState<GPSRData>(DEFAULT_GPSR)

  // Product picker
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([])
  const [dbConvertLoading, setDbConvertLoading] = useState(false)

  // Results
  const [results, setResults] = useState<ConvertResponse | null>(null)
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set())

  // Collapsible sub-sections within step 3
  const [showGpsr, setShowGpsr] = useState(false)
  const [showFaq, setShowFaq] = useState(false)

  // Hooks
  const { data: marketplaces, isLoading: loadingMarketplaces } = useMarketplaces()
  const downloadMutation = useDownloadTemplate()
  const { data: settings } = useSettings()
  const updateSettingsMutation = useUpdateSettings()
  const { toast } = useToast()

  // WHY: Always fetch products — step 1 is the default visible step
  const { data: importedData, isLoading: importedLoading } = useQuery({
    queryKey: ['products', { page_size: 100 }],
    queryFn: () => listProducts({ page_size: 100 }),
    staleTime: 30000,
  })
  const importedProducts = useMemo(() => importedData?.items || [], [importedData])

  // WHY: Auto-fill GPSR from saved settings on mount
  const [gpsrLoaded, setGpsrLoaded] = useState(false)

  useEffect(() => {
    if (!settings?.gpsr || gpsrLoaded) return
    const saved = settings.gpsr
    const hasData = Object.values(saved).some((v) => v !== '')
    if (hasData) setGpsr(saved)
    setGpsrLoaded(true)
  }, [settings, gpsrLoaded])

  const completeStep = useCallback((step: number) => {
    setCompletedSteps((prev) => new Set([...prev, step]))
    if (step < 3) setCurrentStep(step + 1)
  }, [])

  // WHY: Convert products from DB — no scraping, uses data already imported
  const handleConvertFromDb = useCallback(async () => {
    if (selectedProductIds.length === 0 || !marketplace) return
    setDbConvertLoading(true)
    try {
      const res = await apiRequest<ConvertResponse>('post', '/converter/convert-from-db', {
        product_ids: selectedProductIds,
        marketplace,
        gpsr_data: gpsr,
        eur_rate: eurRate,
      })
      if (res.error) throw new Error(res.error)
      setResults(res.data!)
      setExpandedProducts(new Set())
      completeStep(3)
    } catch (err) {
      toast({
        title: 'Błąd konwersji',
        description: err instanceof Error ? err.message : 'Spróbuj ponownie',
        variant: 'destructive',
      })
    } finally {
      setDbConvertLoading(false)
    }
  }, [selectedProductIds, marketplace, gpsr, eurRate, completeStep, toast])

  const handleDownloadFile = useCallback(() => {
    if (selectedProductIds.length === 0 || !marketplace) return
    // WHY: Build synthetic payload from DB products — download template endpoint handles the rest
    const urls = importedProducts
      .filter((p) => selectedProductIds.includes(p.id) && p.source_url)
      .map((p) => p.source_url!)
    if (urls.length > 0) {
      downloadMutation.mutate({
        urls,
        marketplace,
        gpsr_data: gpsr,
        eur_rate: eurRate,
        delay: 2.0,
      })
    } else {
      // WHY: No source URLs = convert from DB directly
      handleConvertFromDb()
    }
  }, [selectedProductIds, marketplace, gpsr, eurRate, importedProducts, downloadMutation, handleConvertFromDb])

  const toggleProduct = (idx: number) => {
    setExpandedProducts((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const updateGpsr = (field: keyof GPSRData, value: string) => {
    setGpsr((prev) => ({ ...prev, [field]: value }))
  }

  const isLoading = downloadMutation.isPending || dbConvertLoading

  return (
    <div className="space-y-6">
      {/* Header + Stepper */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Konwerter → Marketplace</h1>
          <p className="text-sm text-gray-400">
            Przenieś produkty na Amazon, eBay lub Kaufland w 4 krokach
          </p>
        </div>
        <ConverterStepper
          currentStep={currentStep}
          completedSteps={completedSteps}
          onStepClick={setCurrentStep}
        />
      </div>

      {/* Step 1: Select products from DB */}
      {currentStep === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Wybierz produkty</CardTitle>
            <CardDescription>Zaznacz produkty z bazy, które chcesz skonwertować</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {importedLoading ? (
              <div className="flex items-center gap-2 text-sm text-gray-400 py-8 justify-center">
                <Loader2 className="h-4 w-4 animate-spin" />
                Ładowanie produktów...
              </div>
            ) : importedProducts.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <Package className="h-8 w-8 text-gray-600 mx-auto" />
                <p className="text-sm text-gray-400">Brak produktów w bazie</p>
                <p className="text-xs text-gray-600">Zaimportuj produkty w zakładce Import</p>
              </div>
            ) : (
              <>
                {/* Select all / deselect */}
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
                <div className="max-h-80 overflow-y-auto space-y-1">
                  {importedProducts.map((product) => {
                    const isSelected = selectedProductIds.includes(product.id)
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
                        {product.images?.length > 0 ? (
                          <img src={product.images[0]} alt="" className="h-8 w-8 rounded object-cover shrink-0" loading="lazy" />
                        ) : (
                          <div className="h-8 w-8 rounded bg-gray-800 flex items-center justify-center shrink-0">
                            <Package className="h-4 w-4 text-gray-600" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white truncate">{product.title_original}</p>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            {product.brand && <span>{product.brand}</span>}
                            {product.source_platform && <span>{product.source_platform}</span>}
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>

                {/* Next step */}
                <Button
                  onClick={() => completeStep(0)}
                  disabled={selectedProductIds.length === 0}
                  className="w-full"
                >
                  Dalej — wybierz marketplace ({selectedProductIds.length} produktów)
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Choose marketplace */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Gdzie wystawić?</CardTitle>
            <CardDescription>Wybierz marketplace docelowy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
                      <Badge variant="secondary" className="text-[10px]">{mp.extension}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{mp.format}</p>
                  </button>
                ))}
              </div>
            )}
            <Button
              onClick={() => completeStep(1)}
              disabled={!marketplace}
              className="w-full"
            >
              Dalej — ustawienia
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Settings (GPSR + EUR rate) */}
      {currentStep === 2 && (
        <div className="space-y-4">
          {/* EUR Rate */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-white">Kurs EUR (PLN → EUR)</h3>
                  <p className="text-xs text-gray-500">Domyślnie 0.23 — sprawdź aktualny kurs</p>
                </div>
                <Input
                  type="number"
                  step="0.01"
                  value={eurRate}
                  onChange={(e) => setEurRate(parseFloat(e.target.value) || 0.23)}
                  className="w-24 text-right"
                />
              </div>
            </CardContent>
          </Card>

          {/* GPSR */}
          <Card>
            <div className="flex items-center justify-between p-6">
              <button
                onClick={() => setShowGpsr(!showGpsr)}
                className="flex flex-1 items-center justify-between"
              >
                <div>
                  <h3 className="text-sm font-medium text-white">Dane producenta (GPSR)</h3>
                  <p className="text-xs text-gray-500">Wypełnij raz — dotyczy wszystkich produktów</p>
                </div>
                {showGpsr ? (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                )}
              </button>
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
                      <Input value={gpsr.manufacturer_contact} onChange={(e) => updateGpsr('manufacturer_contact', e.target.value)} placeholder="Nazwa producenta" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Adres</label>
                      <Input value={gpsr.manufacturer_address} onChange={(e) => updateGpsr('manufacturer_address', e.target.value)} placeholder="Ulica i numer" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Miasto</label>
                      <Input value={gpsr.manufacturer_city} onChange={(e) => updateGpsr('manufacturer_city', e.target.value)} placeholder="Miasto" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Kraj</label>
                      <Input value={gpsr.manufacturer_country} onChange={(e) => updateGpsr('manufacturer_country', e.target.value)} placeholder="PL, DE, CN..." />
                    </div>
                  </div>
                </div>

                {/* Origin & Safety */}
                <div>
                  <h4 className="mb-3 text-sm font-medium text-gray-300">Pochodzenie i bezpieczeństwo</h4>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Kraj pochodzenia</label>
                      <Input value={gpsr.country_of_origin} onChange={(e) => updateGpsr('country_of_origin', e.target.value)} placeholder="CN, PL, DE..." />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Atest bezpieczeństwa</label>
                      <Input value={gpsr.safety_attestation} onChange={(e) => updateGpsr('safety_attestation', e.target.value)} placeholder="CE, GS..." />
                    </div>
                  </div>
                </div>

                {/* Responsible Person */}
                <div>
                  <h4 className="mb-3 text-sm font-medium text-gray-300">Osoba odpowiedzialna (UE)</h4>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Typ</label>
                      <Input value={gpsr.responsible_person_type} onChange={(e) => updateGpsr('responsible_person_type', e.target.value)} placeholder="Producent / Importer" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Nazwa</label>
                      <Input value={gpsr.responsible_person_name} onChange={(e) => updateGpsr('responsible_person_name', e.target.value)} placeholder="Nazwa firmy" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Adres</label>
                      <Input value={gpsr.responsible_person_address} onChange={(e) => updateGpsr('responsible_person_address', e.target.value)} placeholder="Pełny adres" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Kraj</label>
                      <Input value={gpsr.responsible_person_country} onChange={(e) => updateGpsr('responsible_person_country', e.target.value)} placeholder="DE, PL..." />
                    </div>
                  </div>
                </div>

                {/* Category IDs */}
                <div>
                  <h4 className="mb-3 text-sm font-medium text-gray-300">ID kategorii</h4>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Amazon Browse Node</label>
                      <Input value={gpsr.amazon_browse_node} onChange={(e) => updateGpsr('amazon_browse_node', e.target.value)} placeholder="np. 3169011" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Amazon Product Type</label>
                      <Input value={gpsr.amazon_product_type} onChange={(e) => updateGpsr('amazon_product_type', e.target.value)} placeholder="np. HOME" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">eBay Category ID</label>
                      <Input value={gpsr.ebay_category_id} onChange={(e) => updateGpsr('ebay_category_id', e.target.value)} placeholder="np. 11700" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-gray-500">Kaufland Category</label>
                      <Input value={gpsr.kaufland_category} onChange={(e) => updateGpsr('kaufland_category', e.target.value)} placeholder="np. Haushalt" />
                    </div>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Action buttons */}
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setCurrentStep(1)} className="flex-1">
              Wstecz
            </Button>
            <Button onClick={() => completeStep(2)} className="flex-1">
              Dalej — konwertuj
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Convert + Results */}
      {currentStep === 3 && (
        <div className="space-y-4">
          {/* Action bar */}
          <Card>
            <CardContent className="flex items-center gap-3 py-4">
              <div className="text-sm text-gray-400">
                {selectedProductIds.length} produktów → <span className="text-white font-medium">{marketplace}</span>
              </div>
              <div className="ml-auto flex gap-2">
                <Button
                  onClick={handleConvertFromDb}
                  disabled={isLoading}
                  variant="outline"
                >
                  {dbConvertLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Eye className="mr-2 h-4 w-4" />
                  )}
                  Podgląd
                </Button>
                <Button
                  onClick={handleDownloadFile}
                  disabled={isLoading}
                >
                  {downloadMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-4 w-4" />
                  )}
                  Pobierz plik
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {results && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Wyniki</CardTitle>
                <CardDescription>
                  Skonwertowano {results.succeeded} z {results.total} produktów dla {results.marketplace}
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
      )}

      {/* FAQ — always visible at bottom */}
      <Card>
        <button
          onClick={() => setShowFaq(!showFaq)}
          className="flex w-full items-center justify-between p-6"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5 text-gray-400" />
            <div>
              <h3 className="text-sm font-medium text-white">FAQ — Jak korzystać</h3>
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
              question="Skąd bierze produkty?"
              answer="Konwerter używa produktów z Twojej bazy (zakładka Import). Zaimportuj produkty przez CSV lub Allegro API, a potem wróć tutaj żeby je skonwertować."
            />
            <FaqItem
              question="Co to jest GPSR?"
              answer="General Product Safety Regulation — wymóg UE od 2024. Musisz podać dane producenta, osoby odpowiedzialnej w UE i kraj pochodzenia. Wypełnij raz — dane dotyczą wszystkich produktów."
            />
            <FaqItem
              question="Co to jest kurs EUR?"
              answer="Kurs wymiany PLN → EUR. Domyślnie 0.23 (1 PLN ≈ 0.23 EUR). Sprawdź aktualny kurs przed konwersją."
            />
            <FaqItem
              question="Jak wgrać plik na Amazon?"
              answer="Amazon Seller Central → Catalog → Add Products via Upload → Upload your file (wgraj pobrany TSV). Upewnij się, że wybrałeś właściwy Product Type i Browse Node."
            />
          </CardContent>
        )}
      </Card>
    </div>
  )
}


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
            <p className="text-xs text-gray-500 truncate max-w-md">{product.source_url}</p>
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
          {hasError && (
            <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{product.error}</div>
          )}
          {hasWarnings && (
            <div className="space-y-1">
              {product.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 rounded bg-yellow-500/5 px-3 py-2 text-xs text-yellow-400">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                  {w}
                </div>
              ))}
            </div>
          )}
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
