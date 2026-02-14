// frontend/src/app/products/import/page.tsx
// Purpose: Product import page — single or batch import with tab switching
// NOT for: Product editing, optimization, or publishing

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, ArrowLeft, Package, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'
import SingleImport from './components/SingleImport'
import BatchImport from './components/BatchImport'

const TABS = [
  { id: 'single', label: 'Pojedynczy', icon: Package, desc: 'ASIN, link lub dane ręcznie' },
  { id: 'batch', label: 'Import zbiorczy', icon: Layers, desc: 'CSV z Allegro lub wklej dane' },
] as const

export default function ImportPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('batch')

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Wróć
        </button>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Upload className="h-6 w-6 text-gray-400" />
          Importuj Produkty
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Dodaj produkty z Allegro, eBay lub ręcznie — potem optymalizuj dla Amazon
        </p>
      </div>

      {/* Tab selector */}
      <div className="flex gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex flex-1 items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors',
              activeTab === tab.id
                ? 'border-white/20 bg-white/10 text-white'
                : 'border-gray-800 bg-[#1A1A1A] text-gray-400 hover:border-gray-600 hover:text-white'
            )}
          >
            <tab.icon className="h-5 w-5 shrink-0" />
            <div>
              <div className="text-sm font-medium">{tab.label}</div>
              <div className="text-xs text-gray-500">{tab.desc}</div>
            </div>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'single' ? <SingleImport /> : <BatchImport />}
    </div>
  )
}
