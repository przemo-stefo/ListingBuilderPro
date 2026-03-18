// frontend/src/app/validator/components/ValidatorHistory.tsx
// Purpose: List of past validation runs with delete capability
// NOT for: Running new validations (ValidatorForm.tsx) or displaying details (ValidatorResult.tsx)

'use client'

import { useState, useEffect } from 'react'
import { Loader2, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { getValidatorHistory, deleteValidatorHistory } from '@/lib/api/validator'
import type { ValidatorHistoryItem } from '@/lib/types'

function verdictBadge(verdict: string) {
  const config: Record<string, { label: string; classes: string }> = {
    warto: { label: 'Warto', classes: 'text-green-400 bg-green-900/20' },
    ryzykowne: { label: 'Ryzykowne', classes: 'text-amber-400 bg-amber-900/20' },
    odpusc: { label: 'Odpuść', classes: 'text-red-400 bg-red-900/20' },
  }
  const c = config[verdict] || config.ryzykowne
  return (
    <span className={cn('rounded px-2 py-0.5 text-xs font-medium', c.classes)}>
      {c.label}
    </span>
  )
}

function scoreColor(score: number): string {
  if (score >= 8) return 'text-green-400'
  if (score >= 6) return 'text-amber-400'
  return 'text-red-400'
}

export function ValidatorHistory() {
  const [items, setItems] = useState<ValidatorHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const loadHistory = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await getValidatorHistory(50, 0)
      setItems(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Błąd ładowania historii')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await deleteValidatorHistory(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
      setTotal((prev) => prev - 1)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Błąd usuwania')
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-gray-800">
        <CardContent className="p-4">
          <p className="text-sm text-red-400">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (items.length === 0) {
    return (
      <Card className="border-gray-800">
        <CardContent className="p-6 text-center">
          <p className="text-sm text-gray-400">Brak historii walidacji. Przeprowadź pierwszą analizę.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">{total} walidacji</p>

      {items.map((item) => (
        <Card key={item.id} className="border-gray-800">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                className="flex flex-1 items-center gap-3 text-left"
              >
                <span className={cn('text-lg font-bold', scoreColor(item.score))}>
                  {item.score}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm text-white">{item.product_input}</p>
                  <p className="text-[10px] text-gray-500">
                    {item.marketplace} &middot;{' '}
                    {item.created_at ? new Date(item.created_at).toLocaleDateString('pl-PL') : '—'}
                  </p>
                </div>
                {verdictBadge(item.verdict)}
                {expandedId === item.id ? (
                  <ChevronUp className="h-4 w-4 text-gray-500" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-500" />
                )}
              </button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(item.id)}
                disabled={deletingId === item.id}
                className="ml-2 text-gray-500 hover:text-red-400"
              >
                {deletingId === item.id ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>

            {expandedId === item.id && (
              <div className="mt-3 rounded-md border border-gray-800 bg-[#1A1A1A] p-3">
                <p className="text-xs text-gray-300">{item.explanation}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
