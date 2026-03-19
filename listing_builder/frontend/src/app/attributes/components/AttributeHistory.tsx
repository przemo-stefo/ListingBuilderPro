// frontend/src/app/attributes/components/AttributeHistory.tsx
// Purpose: Past attribute generation runs — expand to see results, delete
// NOT for: Form (AttributeForm.tsx) or result editing (AttributeResult.tsx)

'use client'

import { useState, useEffect } from 'react'
import { Loader2, Trash2, ChevronDown, ChevronRight, Tags } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getAttributeHistory, deleteAttributeHistory } from '@/lib/api/attributes'
import type { AttributeHistoryItem } from '@/lib/types'

export function AttributeHistory() {
  const [items, setItems] = useState<AttributeHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const fetchHistory = async () => {
    setIsLoading(true)
    try {
      const data = await getAttributeHistory(50, 0)
      setItems(data.items)
      setTotal(data.total)
    } catch {
      // silent
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setIsLoading(true)
      try {
        const data = await getAttributeHistory(50, 0)
        if (!cancelled) {
          setItems(data.items)
          setTotal(data.total)
        }
      } catch {
        // silent
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await deleteAttributeHistory(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
      setTotal((prev) => prev - 1)
    } catch {
      // silent
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <Card className="border-gray-800">
        <CardContent className="py-12 text-center">
          <Tags className="mx-auto h-8 w-8 text-gray-600 mb-2" />
          <p className="text-sm text-gray-400">Brak historii generowania atrybutów</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">{total} {total === 1 ? 'wynik' : 'wyników'}</p>
      {items.map((item) => {
        const isExpanded = expandedId === item.id
        return (
          <Card key={item.id} className="border-gray-800">
            <CardContent className="p-0">
              <button
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className="flex w-full items-center justify-between p-4 text-left hover:bg-gray-800/30 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-gray-500 shrink-0" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-500 shrink-0" />
                    )}
                    <span className="text-sm font-medium text-white truncate">{item.product_input}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 ml-6 text-xs text-gray-500">
                    {item.category_name && <span>{item.category_name}</span>}
                    <span>{item.params_count} atrybutów</span>
                    {item.created_at && (
                      <span>{new Date(item.created_at).toLocaleDateString('pl-PL')}</span>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(item.id)
                  }}
                  disabled={deletingId === item.id}
                  className="text-gray-500 hover:text-red-400 shrink-0"
                >
                  {deletingId === item.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </button>

              {isExpanded && item.attributes && item.attributes.length > 0 && (
                <div className="border-t border-gray-800 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-500">
                        <th className="px-4 py-2 font-medium">Atrybut</th>
                        <th className="px-4 py-2 font-medium">Wartość</th>
                        <th className="px-4 py-2 font-medium w-20">Wymagany</th>
                      </tr>
                    </thead>
                    <tbody>
                      {item.attributes.map((attr: Record<string, unknown>, i: number) => (
                        <tr key={i} className="border-t border-gray-800/50">
                          <td className="px-4 py-1.5 text-gray-300">{String(attr.name ?? '')}</td>
                          <td className="px-4 py-1.5 text-white">
                            {attr.value !== null && attr.value !== undefined && attr.value !== ''
                              ? String(attr.value)
                              : <span className="text-xs text-red-400">brak</span>
                            }
                          </td>
                          <td className="px-4 py-1.5 text-center text-xs text-gray-500">
                            {attr.required ? 'Tak' : 'Nie'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
