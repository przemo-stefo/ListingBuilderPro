// frontend/src/app/publish/page.tsx
// Purpose: Publishing page for exporting products to marketplaces
// NOT for: Product editing or optimization

'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useProducts } from '@/lib/hooks/useProducts'
import { listMarketplaces, bulkPublish } from '@/lib/api/export'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/lib/hooks/useToast'
import { cn, getStatusColor, truncate } from '@/lib/utils'
import { Send, CheckCircle2, Globe } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'
import { PremiumGate } from '@/components/tier/PremiumGate'

const PUBLISH_FAQ = [
  { question: 'Co oznacza "Publikacja"?', answer: 'Publikacja eksportuje Twoje zoptymalizowane produkty na wybrany marketplace. Tylko produkty o statusie "zoptymalizowane" są gotowe do publikacji.' },
  { question: 'Jak wybrać produkty do publikacji?', answer: 'Kliknij na kartach produktów aby je zaznaczyć (pojawi się ptaszek). Możesz też użyć "Zaznacz wszystkie" aby wybrać wszystko naraz.' },
  { question: 'Co jeśli publikacja się nie powiedzie?', answer: 'System pokaże które produkty się nie opublikowały i dlaczego. Najczęściej przyczyną jest brak wymaganych pól (np. kategorii lub ceny). Popraw dane i spróbuj ponownie.' },
]

export default function PublishPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  // WHY: product.id is number from backend, but bulkPublish expects string[] — convert on publish
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [selectedMarketplace, setSelectedMarketplace] = useState<string>('')

  // Fetch optimized products ready to publish
  const { data: productsData, isLoading: productsLoading } = useProducts({
    status: 'optimized',
    page_size: 50,
  })

  // Fetch available marketplaces
  const { data: marketplaces, isLoading: marketplacesLoading } = useQuery({
    queryKey: ['marketplaces'],
    queryFn: listMarketplaces,
  })

  // Set default marketplace when loaded
  useEffect(() => {
    if (marketplaces && marketplaces.length > 0 && !selectedMarketplace) {
      setSelectedMarketplace(marketplaces[0].id)
    }
  }, [marketplaces, selectedMarketplace])

  const publishMutation = useMutation({
    // WHY: bulkPublish expects string[] but our IDs are numbers — convert here
    mutationFn: () =>
      bulkPublish(selectedIds.map(String), selectedMarketplace, true),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast({
        title: 'Publikacja zakończona',
        description: `Pomyślnie opublikowano ${result.successful.length} produktów`,
      })
      if (result.failed.length > 0) {
        toast({
          title: 'Niektóre produkty nie zostały opublikowane',
          description: `${result.failed.length} produktów nie udało się opublikować`,
          variant: 'destructive',
        })
      }
      setSelectedIds([])
    },
    onError: (error: Error) => {
      toast({
        title: 'Publikacja nie powiodła się',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const selectAll = () => {
    if (productsData?.items) {
      setSelectedIds(productsData.items.map((p) => p.id))
    }
  }

  const deselectAll = () => {
    setSelectedIds([])
  }

  const handlePublish = () => {
    if (selectedIds.length === 0) {
      toast({
        title: 'Nie zaznaczono produktów',
        description: 'Zaznacz co najmniej jeden produkt do publikacji',
        variant: 'destructive',
      })
      return
    }
    if (!selectedMarketplace) {
      toast({
        title: 'Nie wybrano marketplace\'u',
        description: 'Wybierz marketplace',
        variant: 'destructive',
      })
      return
    }
    publishMutation.mutate()
  }

  const isLoading = productsLoading || marketplacesLoading

  return (
    <PremiumGate feature="Eksport do pliku">
      <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Publikacja na marketplace&apos;y</h1>
        <p className="text-gray-400 mt-2">
          Eksportuj zoptymalizowane produkty na wybrane marketplace&apos;y. Zaznacz produkty i kliknij publikuj.
        </p>
      </div>

      {/* Stats & Marketplace Selection */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Produkty gotowe do publikacji</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {productsData?.total || 0}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Zaznaczono</p>
                <p className="text-3xl font-bold text-green-500 mt-1">
                  {selectedIds.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Wybierz marketplace</CardTitle>
          </CardHeader>
          <CardContent>
            {marketplacesLoading ? (
              <div className="h-10 bg-gray-700 rounded animate-pulse" />
            ) : marketplaces && marketplaces.length > 0 ? (
              <div className="grid gap-2">
                {marketplaces.map((marketplace) => (
                  <button
                    key={marketplace.id}
                    onClick={() => setSelectedMarketplace(marketplace.id)}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg border transition-colors text-left',
                      selectedMarketplace === marketplace.id
                        ? 'border-white bg-[#1A1A1A]'
                        : 'border-gray-700 hover:bg-gray-800'
                    )}
                  >
                    <Globe className="h-5 w-5 text-white" />
                    <div className="flex-1">
                      <p className="font-medium text-white">{marketplace.name}</p>
                      <p className="text-xs text-gray-400">{marketplace.region}</p>
                    </div>
                    {selectedMarketplace === marketplace.id && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Brak dostępnych marketplace&apos;ów</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={selectAll}>
            Zaznacz wszystkie
          </Button>
          <Button variant="outline" size="sm" onClick={deselectAll}>
            Odznacz wszystkie
          </Button>
        </div>
        <Button
          onClick={handlePublish}
          disabled={selectedIds.length === 0 || !selectedMarketplace || publishMutation.isPending}
        >
          <Send className="h-4 w-4 mr-2" />
          {publishMutation.isPending
            ? 'Publikowanie...'
            : `Publikuj ${selectedIds.length} produktów`}
        </Button>
      </div>

      {/* Products List */}
      {isLoading ? (
        <div className="grid gap-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-16 bg-gray-700 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : productsData && productsData.items.length > 0 ? (
        <div className="grid gap-4">
          {productsData.items.map((product) => {
            const isSelected = selectedIds.includes(product.id)
            return (
              <Card
                key={product.id}
                className={cn(
                  'cursor-pointer transition-all hover:border-gray-600',
                  isSelected && 'border-white bg-[#1A1A1A]'
                )}
                onClick={() => toggleSelect(product.id)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div
                      className={cn(
                        'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-1 transition-colors',
                        isSelected
                          ? 'border-white bg-white'
                          : 'border-gray-600'
                      )}
                    >
                      {isSelected && <CheckCircle2 className="h-4 w-4 text-black" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {truncate(product.title_optimized || product.title_original, 80)}
                        </h3>
                        <Badge className={cn('text-xs', getStatusColor(product.status))}>
                          {product.status}
                        </Badge>
                        {product.optimization_score && (
                          <Badge variant="outline" className="text-xs text-green-500">
                            Score: {Math.round(product.optimization_score)}%
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-400">
                        {truncate(product.description_optimized || product.description_original || 'Brak opisu', 120)}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        {product.source_id && <span>ID: {product.source_id}</span>}
                        {product.brand && <span>Marka: {product.brand}</span>}
                        {product.category && <span>Kategoria: {product.category}</span>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Brak gotowych produktów</CardTitle>
            <CardDescription>
              Najpierw zoptymalizuj produkty przed publikacją na marketplace&apos;y.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <FaqSection
        title="Najczęściej zadawane pytania"
        subtitle="Eksport i publikacja"
        items={PUBLISH_FAQ}
      />
      </div>
    </PremiumGate>
  )
}
