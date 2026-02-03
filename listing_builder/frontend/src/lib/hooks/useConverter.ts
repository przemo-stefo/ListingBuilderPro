// frontend/src/lib/hooks/useConverter.ts
// Purpose: React Query hooks for Allegro→Marketplace converter
// NOT for: Direct API calls (those are in lib/api/converter.ts)

import { useQuery, useMutation } from '@tanstack/react-query'
import { getMarketplaces, convertProducts, downloadTemplate } from '../api/converter'
import type { ConvertRequest } from '../types'
import { useToast } from './useToast'

export function useMarketplaces() {
  return useQuery({
    queryKey: ['converter-marketplaces'],
    queryFn: getMarketplaces,
    staleTime: 300_000, // WHY: Marketplace list rarely changes — cache 5 min
  })
}

export function useConvertProducts() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: ConvertRequest) => convertProducts(payload),
    onError: (error: Error) => {
      toast({
        title: 'Conversion failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

// WHY: Separate mutation for download — triggers browser file save via blob URL
export function useDownloadTemplate() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: ConvertRequest) => downloadTemplate(payload),
    onSuccess: (blob, variables) => {
      const ext = variables.marketplace === 'amazon' ? 'tsv' : 'csv'
      const filename = `${variables.marketplace}_template.${ext}`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },
    onError: (error: Error) => {
      toast({
        title: 'Download failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
