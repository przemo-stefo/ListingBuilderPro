// frontend/src/app/video-gen/components/MediaHistoryTab.tsx
// Purpose: History table of past media generations with results, feedback, download
// NOT for: Generation form or output display

'use client'

import { useState } from 'react'
import { Loader2, Download, Trash2, Eye, ChevronLeft, ChevronRight, MessageSquare, Image as ImageIcon, Video } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMediaHistoryList, useDeleteMediaHistory } from '@/lib/hooks/useMediaHistory'
import { getGenerationResult } from '@/lib/api/mediaGeneration'
import { useToast } from '@/lib/hooks/useToast'
import { MediaFeedback } from './MediaFeedback'
import type { ImageResult } from '../types'

interface Props {
  onViewResult?: (result: ImageResult, brand: string) => void
}

export function MediaHistoryTab({ onViewResult }: Props) {
  const [page, setPage] = useState(1)
  const [viewingId, setViewingId] = useState<number | null>(null)
  const [feedbackId, setFeedbackId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const { data, isLoading, error } = useMediaHistoryList(page)
  const deleteMutation = useDeleteMediaHistory()
  const { toast } = useToast()

  const handleView = async (id: number, brand: string) => {
    setViewingId(id)
    try {
      const { result_data } = await getGenerationResult(id)
      if (onViewResult && result_data) {
        onViewResult(result_data as unknown as ImageResult, brand)
      }
    } catch (err) {
      toast({ title: 'Blad ladowania wyniku', description: (err as Error).message, variant: 'destructive' })
    } finally {
      setViewingId(null)
    }
  }

  const handleDownloadAll = async (id: number, brand: string) => {
    try {
      const { result_data } = await getGenerationResult(id)
      const images = (result_data as Record<string, unknown>)?.images as Record<string, string> | undefined
      if (!images) return
      for (const [type, base64] of Object.entries(images)) {
        const link = document.createElement('a')
        link.href = `data:image/png;base64,${base64}`
        link.download = `${brand || 'product'}-${type}.png`
        link.click()
        await new Promise(r => setTimeout(r, 200))
      }
    } catch (err) {
      toast({ title: 'Blad pobierania', description: (err as Error).message, variant: 'destructive' })
    }
  }

  const handleDelete = (id: number) => {
    if (!confirm('Usunac te generacje?')) return
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
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 text-center text-red-400">
        Blad ladowania historii: {(error as Error).message}
      </div>
    )
  }

  if (!data?.items.length) {
    return (
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6 text-center text-gray-500">
        Brak generacji. Wygeneruj wideo lub grafiki aby zobaczyc historie.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">
            Historia generacji
            <span className="ml-2 text-sm font-normal text-gray-500">{data.total} rekordow</span>
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="pb-2 pr-4">Data</th>
                <th className="pb-2 pr-4">Typ</th>
                <th className="pb-2 pr-4">Produkt / URL</th>
                <th className="pb-2 pr-4">Status</th>
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
                  <td className="py-3 pr-4">
                    {item.media_type === 'video' ? (
                      <span className="flex items-center gap-1 text-blue-400 text-xs">
                        <Video className="h-3 w-3" /> Wideo
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-cyan-400 text-xs">
                        <ImageIcon className="h-3 w-3" /> Obrazy
                        {item.image_count ? ` (${item.image_count})` : ''}
                      </span>
                    )}
                  </td>
                  <td className="py-3 pr-4 text-white">
                    {item.product_name ? (
                      <>
                        <div className="max-w-[200px] truncate">{item.product_name}</div>
                        <span className="text-xs text-gray-500">{item.brand}</span>
                      </>
                    ) : (
                      <div className="max-w-[200px] truncate text-xs text-gray-400">{item.url || '—'}</div>
                    )}
                  </td>
                  <td className="py-3 pr-4">
                    <span className={cn(
                      'rounded px-1.5 py-0.5 text-[10px] font-medium',
                      item.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                      item.status === 'running' ? 'bg-amber-500/10 text-amber-400 animate-pulse' :
                      item.status === 'pending' ? 'bg-blue-500/10 text-blue-400' :
                      'bg-red-500/10 text-red-400'
                    )}>
                      {item.status === 'completed' ? 'Gotowe' :
                       item.status === 'running' ? 'Generuje...' :
                       item.status === 'pending' ? 'W kolejce' : 'Blad'}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {item.status === 'completed' && (
                        <>
                          <button
                            onClick={() => handleView(item.id, item.brand)}
                            disabled={viewingId === item.id}
                            className="rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
                            title="Podglad wynikow"
                          >
                            {viewingId === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Eye className="h-3 w-3" />}
                          </button>
                          <button
                            onClick={() => handleDownloadAll(item.id, item.brand)}
                            className="rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
                            title="Pobierz"
                          >
                            <Download className="h-3 w-3" />
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => setFeedbackId(feedbackId === item.id ? null : item.id)}
                        className={cn(
                          'rounded p-1.5 transition-colors',
                          item.feedback ? 'text-cyan-400 hover:bg-gray-800' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                        )}
                        title={item.feedback ? 'Edytuj feedback' : 'Dodaj feedback'}
                      >
                        <MessageSquare className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingId === item.id}
                        className="rounded p-1.5 text-gray-500 hover:bg-gray-800 hover:text-red-400 transition-colors"
                        title="Usun"
                      >
                        {deletingId === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Inline feedback panel */}
        {feedbackId && (
          <div className="mt-4 border-t border-gray-800 pt-4">
            <MediaFeedback
              genId={feedbackId}
              existingFeedback={data.items.find(i => i.id === feedbackId)?.feedback || ''}
              onClose={() => setFeedbackId(null)}
            />
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Strona {page} z {totalPages}</span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="rounded border border-gray-700 p-1.5 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronLeft className="h-3 w-3" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="rounded border border-gray-700 p-1.5 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
