// frontend/src/app/attributes/components/CategoryList.tsx
// Purpose: Category selection list for Auto-Atrybuty form
// NOT for: Search logic (AttributeForm.tsx) or result display (AttributeResult.tsx)

'use client'

import { ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import type { AllegroCategory } from '@/lib/types'

interface CategoryListProps {
  categories: AllegroCategory[]
  selectedId: string | null
  marketplace: 'allegro' | 'kaufland'
  searched: boolean
  onSelect: (cat: AllegroCategory) => void
  onReset: () => void
}

export function CategoryList({ categories, selectedId, marketplace, searched, onSelect, onReset }: CategoryListProps) {
  if (!searched) return null

  if (categories.length === 0) {
    return (
      <Card className="border-gray-800">
        <CardContent className="p-4">
          <p className="text-sm text-gray-400">Nie znaleziono kategorii. Spróbuj inną nazwę produktu.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-gray-800">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-300">
            Wybierz kategorię {marketplace === 'kaufland' ? 'Kaufland' : 'Allegro'}
          </label>
          <button onClick={onReset} className="text-xs text-gray-500 hover:text-gray-300">Zmień</button>
        </div>
        <div className="space-y-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => onSelect(cat)}
              className={`w-full rounded-lg border p-3 text-left transition-colors ${
                selectedId === cat.id
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 bg-[#121212] hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-white">{cat.name}</span>
                  {cat.leaf && (
                    <span className="ml-2 rounded bg-green-500/20 px-1.5 py-0.5 text-[10px] text-green-400">leaf</span>
                  )}
                </div>
                <ChevronRight className="h-4 w-4 text-gray-500" />
              </div>
              <p className="mt-1 text-xs text-gray-500">{cat.path}</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
