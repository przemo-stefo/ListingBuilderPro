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

export default function PublishPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
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
    mutationFn: () =>
      bulkPublish(selectedIds, selectedMarketplace, true),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast({
        title: 'Publishing complete',
        description: `Successfully published ${result.successful.length} product${result.successful.length !== 1 ? 's' : ''}`,
      })
      if (result.failed.length > 0) {
        toast({
          title: 'Some products failed',
          description: `${result.failed.length} product${result.failed.length !== 1 ? 's' : ''} failed to publish`,
          variant: 'destructive',
        })
      }
      setSelectedIds([])
    },
    onError: (error: Error) => {
      toast({
        title: 'Publishing failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const toggleSelect = (id: string) => {
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
        title: 'No products selected',
        description: 'Please select at least one product to publish',
        variant: 'destructive',
      })
      return
    }
    if (!selectedMarketplace) {
      toast({
        title: 'No marketplace selected',
        description: 'Please select a marketplace',
        variant: 'destructive',
      })
      return
    }
    publishMutation.mutate()
  }

  const isLoading = productsLoading || marketplacesLoading

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Publish to Marketplaces</h1>
        <p className="text-gray-400 mt-2">
          Export your optimized products to various marketplaces
        </p>
      </div>

      {/* Stats & Marketplace Selection */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Products Ready to Publish</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {productsData?.total || 0}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Selected</p>
                <p className="text-3xl font-bold text-green-500 mt-1">
                  {selectedIds.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Marketplace</CardTitle>
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
              <p className="text-sm text-gray-400">No marketplaces available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={selectAll}>
            Select All
          </Button>
          <Button variant="outline" size="sm" onClick={deselectAll}>
            Deselect All
          </Button>
        </div>
        <Button
          onClick={handlePublish}
          disabled={selectedIds.length === 0 || !selectedMarketplace || publishMutation.isPending}
        >
          <Send className="h-4 w-4 mr-2" />
          {publishMutation.isPending
            ? 'Publishing...'
            : `Publish ${selectedIds.length} Product${selectedIds.length !== 1 ? 's' : ''}`}
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
                          {truncate(product.title, 80)}
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
                        {truncate(product.description || 'No description', 120)}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        {product.asin && <span>ASIN: {product.asin}</span>}
                        {product.brand && <span>Brand: {product.brand}</span>}
                        {product.category && <span>Category: {product.category}</span>}
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
            <CardTitle>No Products Ready</CardTitle>
            <CardDescription>
              Optimize your products first before publishing to marketplaces.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  )
}
