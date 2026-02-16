// frontend/src/app/products/import/page.tsx
// Purpose: Product import page — single or batch import with tab switching
// NOT for: Product editing, optimization, or publishing

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, ArrowLeft, Package, Layers, HelpCircle, ChevronDown, ChevronRight } from 'lucide-react'
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

      {/* FAQ */}
      <ImportFaq />
    </div>
  )
}

function ImportFaq() {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between p-5"
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-gray-400" />
          <div className="text-left">
            <h3 className="text-sm font-semibold text-white">FAQ — Import vs. Converter</h3>
            <p className="text-xs text-gray-500">Czym się różnią i kiedy którego używać</p>
          </div>
        </div>
        {open ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>
      {open && (
        <div className="space-y-3 px-5 pb-5">
          <FaqItem
            question="Czym się różni Import od Convertera?"
            answer="Import zapisuje produkty do bazy danych systemu — możesz je potem przeglądać, edytować i optymalizować listingi AI. Converter to bezpośrednia konwersja Allegro→Amazon/eBay/Kaufland — od razu dostajesz plik TSV/CSV do uploadu, bez zapisu do bazy."
          />
          <FaqItem
            question="Kiedy używać Importu?"
            answer="Gdy chcesz: (1) budować bazę produktów w systemie, (2) korzystać z AI Optimizer do generowania tytułów, bulletów i opisów, (3) śledzić historię optymalizacji, (4) porównywać wersje listingów. Import → Optimize → Publish to pełny pipeline."
          />
          <FaqItem
            question="Kiedy używać Convertera?"
            answer="Gdy chcesz szybko przenieść oferty z Allegro na inny marketplace. Wpisujesz URLe lub nazwę sklepu → system scrapuje, tłumaczy na niemiecki i generuje gotowy plik do uploadu. Bez zapisywania do bazy — szybka konwersja na jedno kliknięcie."
          />
          <FaqItem
            question="Co robi 'Import zbiorczy'?"
            answer="Wklejasz CSV z danymi produktów (tytuł, cena, numer oferty, marka) lub wgrywasz plik. System parsuje dane i tworzy produkty w bazie. Obsługuje polskie i angielskie nagłówki. Limit: 500 produktów na raz."
          />
          <FaqItem
            question="Skąd wziąć CSV z Allegro?"
            answer="W Allegro Seller Center → Moje oferty → Eksportuj do pliku. Możesz też ręcznie utworzyć CSV z kolumnami: tytuł, cena, numer oferty, marka, kategoria, opis, url."
          />
        </div>
      )}
    </div>
  )
}

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-gray-800 bg-[#151515]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-gray-300">{question}</span>
        {open ? (
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-gray-500" />
        ) : (
          <ChevronRight className="ml-2 h-4 w-4 shrink-0 text-gray-500" />
        )}
      </button>
      {open && (
        <p className="px-4 pb-3 text-sm text-gray-500 leading-relaxed">{answer}</p>
      )}
    </div>
  )
}
