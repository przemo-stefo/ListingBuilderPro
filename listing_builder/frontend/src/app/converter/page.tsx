// frontend/src/app/converter/page.tsx
// Purpose: Allegro→Marketplace converter page — scrape, translate, map, download
// NOT for: API logic (that's in lib/api/converter.ts and hooks/useConverter.ts)

'use client'

import { useState } from 'react'
import {
  ArrowRightLeft,
  ChevronDown,
  ChevronRight,
  Download,
  Eye,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useMarketplaces, useConvertProducts, useDownloadTemplate } from '@/lib/hooks/useConverter'
import type { ConvertRequest, ConvertResponse, ConvertedProductResult, GPSRData } from '@/lib/types'

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

  // Results
  const [results, setResults] = useState<ConvertResponse | null>(null)
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set())

  // Hooks
  const { data: marketplaces, isLoading: loadingMarketplaces } = useMarketplaces()
  const convertMutation = useConvertProducts()
  const downloadMutation = useDownloadTemplate()

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

  const handlePreview = () => {
    convertMutation.mutate(buildPayload(), {
      onSuccess: (data) => {
        setResults(data)
        setExpandedProducts(new Set())
      },
    })
  }

  const handleDownload = () => {
    downloadMutation.mutate(buildPayload())
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

  const isLoading = convertMutation.isPending || downloadMutation.isPending

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Converter</h1>
        <p className="text-sm text-gray-400">
          Convert Allegro products to Amazon, eBay, or Kaufland templates
        </p>
      </div>

      {/* Section 1: Allegro URLs */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Allegro URLs</CardTitle>
          </div>
          <CardDescription>Paste Allegro product URLs, one per line (max 50)</CardDescription>
        </CardHeader>
        <CardContent>
          <textarea
            value={urlsText}
            onChange={(e) => setUrlsText(e.target.value)}
            placeholder="https://allegro.pl/oferta/example-product-123456789&#10;https://allegro.pl/oferta/another-product-987654321"
            rows={5}
            className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-gray-600 focus:outline-none focus:ring-1 focus:ring-gray-600"
          />
          <p className="mt-1 text-xs text-gray-500">
            {parseUrls().length} URL{parseUrls().length !== 1 ? 's' : ''} entered
          </p>
        </CardContent>
      </Card>

      {/* Section 2: Target Marketplace */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Target Marketplace</CardTitle>
          <CardDescription>Select where to list these products</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingMarketplaces ? (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading marketplaces...
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
            <h3 className="text-lg font-semibold text-white">Settings</h3>
            <p className="text-sm text-gray-400">Exchange rate and scraping delay</p>
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
                EUR exchange rate (PLN → EUR)
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
                Delay between requests (seconds)
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
        <button
          onClick={() => setShowGpsr(!showGpsr)}
          className="flex w-full items-center justify-between p-6"
        >
          <div>
            <h3 className="text-lg font-semibold text-white">GPSR / Category Data</h3>
            <p className="text-sm text-gray-400">Manufacturer, responsible person, and category IDs</p>
          </div>
          {showGpsr ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </button>
        {showGpsr && (
          <CardContent className="space-y-6">
            {/* Manufacturer */}
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-300">Manufacturer</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Contact</label>
                  <Input
                    value={gpsr.manufacturer_contact}
                    onChange={(e) => updateGpsr('manufacturer_contact', e.target.value)}
                    placeholder="Manufacturer name"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Address</label>
                  <Input
                    value={gpsr.manufacturer_address}
                    onChange={(e) => updateGpsr('manufacturer_address', e.target.value)}
                    placeholder="Street address"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">City</label>
                  <Input
                    value={gpsr.manufacturer_city}
                    onChange={(e) => updateGpsr('manufacturer_city', e.target.value)}
                    placeholder="City"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Country</label>
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
              <h4 className="mb-3 text-sm font-medium text-gray-300">Origin & Safety</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Country of Origin</label>
                  <Input
                    value={gpsr.country_of_origin}
                    onChange={(e) => updateGpsr('country_of_origin', e.target.value)}
                    placeholder="CN, PL, DE..."
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Safety Attestation</label>
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
              <h4 className="mb-3 text-sm font-medium text-gray-300">Responsible Person (EU)</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Type</label>
                  <Input
                    value={gpsr.responsible_person_type}
                    onChange={(e) => updateGpsr('responsible_person_type', e.target.value)}
                    placeholder="Manufacturer / Importer"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Name</label>
                  <Input
                    value={gpsr.responsible_person_name}
                    onChange={(e) => updateGpsr('responsible_person_name', e.target.value)}
                    placeholder="Company name"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Address</label>
                  <Input
                    value={gpsr.responsible_person_address}
                    onChange={(e) => updateGpsr('responsible_person_address', e.target.value)}
                    placeholder="Full address"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Country</label>
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
              <h4 className="mb-3 text-sm font-medium text-gray-300">Category IDs</h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Amazon Browse Node</label>
                  <Input
                    value={gpsr.amazon_browse_node}
                    onChange={(e) => updateGpsr('amazon_browse_node', e.target.value)}
                    placeholder="e.g. 3169011"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Amazon Product Type</label>
                  <Input
                    value={gpsr.amazon_product_type}
                    onChange={(e) => updateGpsr('amazon_product_type', e.target.value)}
                    placeholder="e.g. HOME"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">eBay Category ID</label>
                  <Input
                    value={gpsr.ebay_category_id}
                    onChange={(e) => updateGpsr('ebay_category_id', e.target.value)}
                    placeholder="e.g. 11700"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">Kaufland Category</label>
                  <Input
                    value={gpsr.kaufland_category}
                    onChange={(e) => updateGpsr('kaufland_category', e.target.value)}
                    placeholder="e.g. Haushalt"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Action Bar */}
      <div className="flex items-center gap-3">
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
          Preview
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
          Download Template
        </Button>
        {isLoading && (
          <span className="text-xs text-gray-500">
            This may take a while for multiple URLs...
          </span>
        )}
      </div>

      {/* Section 5: Results */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Results</CardTitle>
            <CardDescription>
              Converted {results.succeeded} of {results.total} products for{' '}
              {results.marketplace}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary badges */}
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-1 rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400">
                <CheckCircle className="h-3 w-3" />
                {results.succeeded} succeeded
              </div>
              {results.failed > 0 && (
                <div className="flex items-center gap-1 rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-400">
                  <XCircle className="h-3 w-3" />
                  {results.failed} failed
                </div>
              )}
              {results.warnings.length > 0 && (
                <div className="flex items-center gap-1 rounded-full bg-yellow-500/10 px-3 py-1 text-xs text-yellow-400">
                  <AlertTriangle className="h-3 w-3" />
                  {results.warnings.length} warnings
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
              Product {index + 1}
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
              {product.warnings.length} warnings
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
                    <th className="pb-2 pr-4 text-left font-medium text-gray-400">Field</th>
                    <th className="pb-2 text-left font-medium text-gray-400">Value</th>
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
