// frontend/src/lib/hooks/useProducts.ts
// Purpose: React Query hooks for product data fetching and mutations
// NOT for: Direct API calls (those are in lib/api/products.ts)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listProducts, getProduct, deleteProduct, getDashboardStats } from '../api/products'
import type { ProductFilters } from '../types'
import { useToast } from './useToast'

// Hook to list products with filters
export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => listProducts(filters),
    // Refetch on window focus to keep data fresh
    staleTime: 30000, // 30 seconds
  })
}

// Hook to get single product
export function useProduct(id: string) {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => getProduct(id),
    enabled: !!id, // Only fetch if ID exists
  })
}

// Hook to delete product with optimistic updates
export function useDeleteProduct() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: deleteProduct,
    onSuccess: (_, productId) => {
      // Invalidate product list to refetch
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })

      toast({
        title: 'Product deleted',
        description: 'Product has been successfully deleted.',
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Delete failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

// Hook to get dashboard stats
export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    staleTime: 60000, // 1 minute
  })
}
