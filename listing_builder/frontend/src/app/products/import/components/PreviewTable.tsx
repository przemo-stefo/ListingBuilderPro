// frontend/src/app/products/import/components/PreviewTable.tsx
// Purpose: Preview table for parsed batch import products
// NOT for: Data parsing or API calls

import { Trash2 } from 'lucide-react'
import type { ParsedProduct } from '../constants'

interface Props {
  products: ParsedProduct[]
  onRemove: (idx: number) => void
  onClear: () => void
}

export default function PreviewTable({ products, onRemove, onClear }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
        <span className="text-sm font-medium text-white">
          Podgląd: {products.length} produktów
        </span>
        <button onClick={onClear}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors">
          Wyczyść
        </button>
      </div>
      <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#1A1A1A] border-b border-gray-800">
            <tr className="text-left text-gray-500">
              <th className="px-4 py-2 w-8">#</th>
              <th className="px-4 py-2">Tytuł</th>
              <th className="px-4 py-2 w-24">Cena</th>
              <th className="px-4 py-2 w-28">ID</th>
              <th className="px-4 py-2 w-24">Marka</th>
              <th className="px-4 py-2 w-10"></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p, i) => (
              <tr key={i} className="border-b border-gray-800/50 hover:bg-white/5">
                <td className="px-4 py-2 text-gray-600">{i + 1}</td>
                <td className="px-4 py-2 text-white truncate max-w-[300px]">{p.title}</td>
                <td className="px-4 py-2 text-gray-300">{p.price ?? '—'}</td>
                <td className="px-4 py-2 text-gray-400 font-mono text-xs">{p.source_id}</td>
                <td className="px-4 py-2 text-gray-400">{p.brand || '—'}</td>
                <td className="px-4 py-2">
                  <button onClick={() => onRemove(i)}
                    className="text-gray-600 hover:text-red-400 transition-colors">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
