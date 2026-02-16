// frontend/src/app/optimize/components/HistoryTab.tsx
// Purpose: Table of past optimization runs — load, download, delete
// NOT for: Running new optimizations (that's SingleTab/BatchTab)

'use client'

import { useState } from 'react'
import { Loader2, Download, Trash2, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useHistoryList, useDeleteHistory } from '@/lib/hooks/useOptimizerHistory'
import { getHistoryDetail } from '@/lib/api/optimizerHistory'
import { downloadCSV } from './ResultDisplay'
import type { OptimizerResponse } from '@/lib/types'

interface HistoryTabProps {
  onLoadResult: (result: OptimizerResponse) => void
}

export default function HistoryTab({ onLoadResult }: HistoryTabProps) {
  const [page, setPage] = useState(1)
  const [loadingId, setLoadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const { data, isLoading, error } = useHistoryList(page)
  const deleteMutation = useDeleteHistory()

  const handleLoad = async (id: number) => {
    setLoadingId(id)
    try {
      const detail = await getHistoryDetail(id)
      onLoadResult(detail.response_data)
    } catch {
      // Toast handled by error boundary
    } finally {
      setLoadingId(null)
    }
  }

  const handleDownload = async (id: number) => {
    try {
      const detail = await getHistoryDetail(id)
      downloadCSV(detail.response_data)
    } catch {
      // Silently fail — user will see nothing downloaded
    }
  }

  const handleDelete = (id: number) => {
    if (!confirm('Usunac te optymalizacje?')) return
    setDeletingId(id)
    deleteMutation.mutate(id, { onSettled: () => setDeletingId(null) })
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-red-400">
          Blad ladowania historii: {error.message}
        </CardContent>
      </Card>
    )
  }

  if (!data?.items.length) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          Brak optymalizacji. Wygeneruj listing najpierw.
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Historia optymalizacji
          <span className="ml-2 text-sm font-normal text-gray-500">
            {data.total} {data.total === 1 ? 'rekord' : data.total < 5 ? 'rekordy' : 'rekordow'}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="pb-2 pr-4">Data</th>
                <th className="pb-2 pr-4">Produkt</th>
                <th className="pb-2 pr-4">Marketplace</th>
                <th className="pb-2 pr-4">Pokrycie</th>
                <th className="pb-2 pr-4">Zgodnosc</th>
                <th className="pb-2 text-right">Akcje</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id} className="border-b border-gray-800/50 hover:bg-white/[0.02]">
                  <td className="py-3 pr-4 text-xs text-gray-400">
                    {new Date(item.created_at).toLocaleDateString('pl-PL', {
                      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
                    })}
                  </td>
                  <td className="py-3 pr-4 text-white">
                    <div className="max-w-[200px] truncate">{item.product_title}</div>
                    <span className="text-xs text-gray-500">{item.brand}</span>
                  </td>
                  <td className="py-3 pr-4 text-gray-400">{item.marketplace}</td>
                  <td className="py-3 pr-4">
                    <span className={cn(
                      'font-medium',
                      item.coverage_pct >= 96 ? 'text-green-400' :
                      item.coverage_pct >= 82 ? 'text-yellow-400' : 'text-red-400'
                    )}>
                      {item.coverage_pct}%
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <Badge variant="secondary" className={cn(
                      'text-[10px]',
                      item.compliance_status === 'PASS' ? 'bg-green-500/10 text-green-400' :
                      item.compliance_status === 'WARNING' ? 'bg-yellow-500/10 text-yellow-400' :
                      'bg-red-500/10 text-red-400'
                    )}>
                      {item.compliance_status}
                    </Badge>
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleLoad(item.id)}
                        disabled={loadingId === item.id}
                        title="Zaladuj wyniki"
                      >
                        {loadingId === item.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <ArrowRight className="h-3 w-3" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(item.id)}
                        title="Pobierz CSV"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingId === item.id}
                        className="text-gray-500 hover:text-red-400"
                        title="Usun"
                      >
                        {deletingId === item.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Strona {page} z {totalPages}
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
