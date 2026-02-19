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
import { FaqSection } from '@/components/ui/FaqSection'

const TABS = [
  { id: 'single', label: 'Pojedynczy', icon: Package, desc: 'ASIN, link lub dane ręcznie' },
  { id: 'batch', label: 'Import zbiorczy', icon: Layers, desc: 'CSV z Allegro lub wklej dane' },
] as const

export default function ImportPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('batch')

  return (
    <div className="space-y-6">
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
      <FaqSection
        title="FAQ — Import vs. Converter"
        subtitle="Czym sie roznia i kiedy ktorego uzywac"
        items={[
          { question: 'Czym sie rozni Import od Convertera?', answer: 'Import zapisuje produkty do bazy danych systemu — mozesz je potem przegladac, edytowac i optymalizowac listingi AI. Converter to bezposrednia konwersja Allegro→Amazon/eBay/Kaufland — od razu dostajesz plik TSV/CSV do uploadu, bez zapisu do bazy.' },
          { question: 'Kiedy uzywac Importu?', answer: 'Gdy chcesz: (1) budowac baze produktow w systemie, (2) korzystac z AI Optimizer do generowania tytulow, bulletow i opisow, (3) sledzic historie optymalizacji, (4) porownywac wersje listingow. Import → Optimize → Publish to pelny pipeline.' },
          { question: 'Kiedy uzywac Convertera?', answer: 'Gdy chcesz szybko przeniesc oferty z Allegro na inny marketplace. Wpisujesz URLe lub nazwe sklepu → system scrapuje, tlumaczy na niemiecki i generuje gotowy plik do uploadu. Bez zapisywania do bazy — szybka konwersja na jedno klikniecie.' },
          { question: 'Co robi Import zbiorczy?', answer: 'Wklejasz CSV z danymi produktow (tytul, cena, numer oferty, marka) lub wgrywasz plik. System parsuje dane i tworzy produkty w bazie. Obsluguje polskie i angielskie naglowki. Limit: 500 produktow na raz.' },
          { question: 'Skad wziac CSV z Allegro?', answer: 'W Allegro Seller Center → Moje oferty → Eksportuj do pliku. Mozesz tez recznie utworzyc CSV z kolumnami: tytul, cena, numer oferty, marka, kategoria, opis, url.' },
        ]}
      />
    </div>
  )
}
