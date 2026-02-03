// frontend/src/app/optimize/page.tsx
// Purpose: AI optimization page for bulk optimization of products
// NOT for: Single product optimization (that's in product detail)

'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useProducts } from '@/lib/hooks/useProducts'
import { batchOptimize } from '@/lib/api/ai'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/lib/hooks/useToast'
import { cn, getStatusColor, truncate } from '@/lib/utils'
import { Sparkles, CheckCircle2 } from 'lucide-react'

export default function OptimizePage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  // Fetch pending and unoptimized products
  const { data, isLoading } = useProducts({
    status: 'pending',
    page_size: 50,
  })

  const optimizeMutation = useMutation({
    mutationFn: () =>
      batchOptimize({
        product_ids: selectedIds,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast({
        title: 'Batch optimization started',
        description: `Processing ${result.total_products} products`,
      })
      setSelectedIds([])
    },
    onError: (error: Error) => {
      toast({
        title: 'Optimization failed',
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
    if (data?.items) {
      setSelectedIds(data.items.map((p) => p.id))
    }
  }

  const deselectAll = () => {
    setSelectedIds([])
  }

  const handleOptimize = () => {
    if (selectedIds.length === 0) {
      toast({
        title: 'No products selected',
        description: 'Please select at least one product to optimize',
        variant: 'destructive',
      })
      return
    }
    optimizeMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">AI Optimization</h1>
        <p className="text-gray-400 mt-2">
          Optimize product listings with AI-powered suggestions
        </p>
      </div>

      {/* Stats Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Products Ready for Optimization</p>
              <p className="text-3xl font-bold text-white mt-1">
                {data?.total || 0}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Selected</p>
              <p className="text-3xl font-bold text-blue-500 mt-1">
                {selectedIds.length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

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
          onClick={handleOptimize}
          disabled={selectedIds.length === 0 || optimizeMutation.isPending}
        >
          <Sparkles className="h-4 w-4 mr-2" />
          {optimizeMutation.isPending
            ? 'Optimizing...'
            : `Optimize ${selectedIds.length} Product${selectedIds.length !== 1 ? 's' : ''}`}
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
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((product) => {
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
                      </div>
                      <p className="text-sm text-gray-400">
                        {truncate(product.description || 'No description', 120)}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        {product.asin && <span>ASIN: {product.asin}</span>}
                        {product.brand && <span>Brand: {product.brand}</span>}
                        {product.marketplace && <span>Market: {product.marketplace}</span>}
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
            <CardTitle>No Products to Optimize</CardTitle>
            <CardDescription>
              All products are already optimized. Import new products to get started.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  )
}
