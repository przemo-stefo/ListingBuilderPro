// frontend/src/app/optimize/page.tsx
// Purpose: Listing Optimizer page — orchestrator with Single/Batch/History tab switching
// NOT for: Form logic or result display (those are in components/)

'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layers, FileText, Clock, Crown, Loader2 } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useToast } from '@/lib/hooks/useToast'
import SingleTab from './components/SingleTab'
import BatchTab from './components/BatchTab'
import HistoryTab from './components/HistoryTab'
import type { OptimizerResponse } from '@/lib/types'

type Tab = 'single' | 'batch' | 'history'

// WHY: Next.js 14 requires Suspense boundary around useSearchParams()
function OptimizeContent() {
  const searchParams = useSearchParams()
  // WHY: Allegro Manager "Optymalizuj z AI" passes ?prefill=title
  const prefillTitle = searchParams.get('prefill') ?? undefined
  // WHY: When coming from product detail page, we pass product_id so optimizer can save back
  const productId = searchParams.get('product_id') ?? undefined
  const [activeTab, setActiveTab] = useState<Tab>('single')
  // WHY: When user clicks "Load" in History, we switch to Single and pass the result
  const [loadedResult, setLoadedResult] = useState<OptimizerResponse | null>(null)
  const { isPremium } = useTier()
  const { toast } = useToast()

  const handleLoadFromHistory = (result: OptimizerResponse) => {
    setLoadedResult(result)
    setActiveTab('single')
  }

  const handleHistoryClick = () => {
    if (!isPremium) {
      toast({
        title: 'Historia — Premium',
        description: 'Historia optymalizacji jest dostępna w planie Premium.',
        variant: 'destructive',
      })
      return
    }
    setActiveTab('history')
  }

  return (
    <div className="space-y-6">
      {/* Page header + tab toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Optymalizator listingów</h1>
          <p className="text-sm text-gray-400">
            Generuj zoptymalizowane tytuły, bullety, opisy i słowa kluczowe backend
          </p>
        </div>

        {/* Tab toggle */}
        <div className="flex rounded-lg border border-gray-800 p-1">
          <button
            onClick={() => { setActiveTab('single'); setLoadedResult(null) }}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'single'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <FileText className="h-4 w-4" />
            Pojedyncze
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'batch'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Layers className="h-4 w-4" />
            Zbiorowe
          </button>
          <button
            onClick={handleHistoryClick}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'history'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <Clock className="h-4 w-4" />
            Historia
            {!isPremium && <Crown className="h-3 w-3 text-amber-400" />}
          </button>
        </div>
      </div>

      {/* Active tab content */}
      {activeTab === 'single' && <SingleTab loadedResult={loadedResult} initialTitle={prefillTitle} productId={productId} />}
      {activeTab === 'batch' && <BatchTab />}
      {activeTab === 'history' && isPremium && <HistoryTab onLoadResult={handleLoadFromHistory} />}

      <FaqSection
        title="FAQ — Optymalizator"
        subtitle="Najczęściej zadawane pytania o optymalizacji listingów"
        items={[
          { question: 'Jak działa optymalizator?', answer: 'Wpisujesz tytuł produktu (lub importujesz z CSV/Allegro), wybierasz marketplace i język, a AI generuje zoptymalizowany tytuł, 5 bullet pointów, opis i backend keywords. Każdy element jest dostosowany do wymagań danego marketplace.' },
          { question: 'Co to jest Ranking Juice?', answer: 'Ranking Juice to wynik 0-100 oceniający jakość Twojego listingu. Analizuje tytuł (długość, słowa kluczowe), bullety (struktura, benefity), opis (SEO, czytelność) i backend keywords (unikatowe frazy). Im wyższy wynik, tym lepsza widoczność w wyszukiwarce marketplace.' },
          { question: 'Jaka jest różnica między trybem agresywnym a standardowym?', answer: 'Tryb standardowy generuje naturalne, czytelne listingi. Tryb agresywny maksymalizuje nasycenie słów kluczowych — tytuł i bullety są bardziej "keyword-stuffed". Użyj agresywnego dla produktów w konkurencyjnych kategoriach.' },
          { question: 'Ile kosztuje jedna optymalizacja?', answer: 'Plan darmowy: 3 optymalizacje dziennie (tylko Amazon). Plan Premium (49 PLN/mieś): nieograniczone optymalizacje na wszystkich marketplace (Amazon, eBay, Kaufland, Allegro).' },
          { question: 'Jak pobrać wynik jako CSV?', answer: 'Po optymalizacji kliknij przycisk "Eksportuj CSV" nad wynikiem. Plik zawiera tytuł, bullety, opis i backend keywords — gotowy do uploadu na marketplace lub do flat file.' },
          { question: 'Co to jest "Model AI" w sekcji Cel i tryb?', answer: 'To silnik sztucznej inteligencji generujacy listing. Domyslnie uzywamy Groq (Llama 3.3 70B) — jest darmowy i wliczony w cene. Jesli chcesz lepszej jakosci, mozesz wybrac Gemini Pro lub OpenAI (wymagaja Twojego klucza API). Klucz zapisujesz w Ustawienia → Model AI.' },
          { question: 'Jaka jest roznica miedzy Groq, Gemini i OpenAI?', answer: 'Groq (Llama 3.3): darmowy, dobra jakosc, najszybszy. Gemini Flash: tani, szybki, nieco lepsza jakosc. Gemini Pro: najlepsza jakosc tekstu, wolniejszy, drozszy. OpenAI (GPT-4o Mini): dobra jakosc, srednia cena. Jesli nie wiesz co wybrac — zostaw Groq, jest wystarczajaco dobry.' },
        ]}
      />
    </div>
  )
}

export default function OptimizePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    }>
      <OptimizeContent />
    </Suspense>
  )
}
