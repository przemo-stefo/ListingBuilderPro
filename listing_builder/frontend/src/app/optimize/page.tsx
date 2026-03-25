// frontend/src/app/optimize/page.tsx
// Purpose: Listing Optimizer page — orchestrator with Single/Batch/History tab switching
// NOT for: Form logic or result display (those are in components/)

'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layers, FileText, Clock, Crown, Loader2, ArrowLeftRight, Sparkles } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'
import { FlowIndicator } from '@/components/ui/FlowIndicator'
import { cn } from '@/lib/utils'
import { useTier } from '@/lib/hooks/useTier'
import { useDashboardStats } from '@/lib/hooks/useProducts'
import { useToast } from '@/lib/hooks/useToast'
import dynamic from 'next/dynamic'

const SingleTab = dynamic(() => import('./components/SingleTab'), {
  loading: () => <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-gray-500" /></div>,
})
const BatchTab = dynamic(() => import('./components/BatchTab'), {
  loading: () => <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-gray-500" /></div>,
})
const HistoryTab = dynamic(() => import('./components/HistoryTab'), {
  loading: () => <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-gray-500" /></div>,
})
const ABTestTab = dynamic(() => import('./components/ABTestTab'), {
  loading: () => <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-gray-500" /></div>,
})
import type { OptimizerResponse } from '@/lib/types'

type Tab = 'single' | 'batch' | 'abtest' | 'history'

// WHY: Next.js 14 requires Suspense boundary around useSearchParams()
function OptimizeContent() {
  const searchParams = useSearchParams()
  // WHY: Allegro Manager "Optymalizuj z AI" passes ?prefill=title
  const prefillTitle = searchParams.get('prefill') ?? undefined
  // WHY: When coming from product detail page, we pass product_id so optimizer can save back
  const productId = searchParams.get('product_id') ?? undefined
  // WHY: ?tab=batch from products page "Zoptymalizuj wszystkie" link
  const initialTab = searchParams.get('tab') as Tab | null
  const [activeTab, setActiveTab] = useState<Tab>(initialTab === 'batch' ? 'batch' : 'single')
  // WHY: When user clicks "Load" in History, we switch to Single and pass the result
  const [loadedResult, setLoadedResult] = useState<OptimizerResponse | null>(null)
  const { isPremium } = useTier()
  const { toast } = useToast()
  const { data: dashStats } = useDashboardStats()

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
      {/* WHY: Flow indicator — user sees where they are in the 3-step workflow */}
      <FlowIndicator stats={dashStats ?? null} currentStep="optimize" />

      {/* Page header + tab toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Sparkles className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Optymalizator listingów</h1>
            <p className="text-sm text-gray-400">
              Generuj zoptymalizowane tytuły, bullety, opisy i słowa kluczowe backend
            </p>
          </div>
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
            onClick={() => setActiveTab('abtest')}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors',
              activeTab === 'abtest'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white'
            )}
          >
            <ArrowLeftRight className="h-4 w-4" />
            A/B Test
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
      {activeTab === 'abtest' && <ABTestTab />}
      {activeTab === 'history' && isPremium && <HistoryTab onLoadResult={handleLoadFromHistory} />}

      <FaqSection
        title="FAQ — Optymalizator"
        subtitle="Najczęściej zadawane pytania o optymalizacji listingów"
        items={[
          { question: 'Jak działa optymalizator?', answer: 'Wpisujesz tytuł produktu (lub importujesz z CSV/Allegro), wybierasz marketplace i język, a AI generuje zoptymalizowany tytuł, 5 bullet pointów, opis i backend keywords. Każdy element jest dostosowany do wymagań danego marketplace.' },
          { question: 'Co to jest Ranking Juice?', answer: 'Ranking Juice to wynik 0-100 oceniający jakość Twojego listingu. Analizuje tytuł (długość, słowa kluczowe), bullety (struktura, benefity), opis (SEO, czytelność) i backend keywords (unikatowe frazy). Im wyższy wynik, tym lepsza widoczność w wyszukiwarce marketplace.' },
          { question: 'Jaka jest różnica między trybem agresywnym a standardowym?', answer: 'Tryb standardowy generuje naturalne, czytelne listingi. Tryb agresywny maksymalizuje nasycenie słów kluczowych — tytuł i bullety są bardziej "keyword-stuffed". Użyj agresywnego dla produktów w konkurencyjnych kategoriach.' },
          { question: 'Ile kosztuje jedna optymalizacja?', answer: 'Subskrypcja OctoHelper (19,00 PLN/mies) daje Ci Optymalizator bez limitów na wszystkie marketplace, Import produktów, Konwerter ofert, Listing Score, Walidator Produktu, Ekspert Kaufland i Auto-Atrybuty.' },
          { question: 'Jak pobrać wynik jako CSV?', answer: 'Po optymalizacji kliknij przycisk "Eksportuj CSV" nad wynikiem. Plik zawiera tytuł, bullety, opis i backend keywords — gotowy do uploadu na marketplace lub do flat file.' },
          { question: 'Co to jest "Model AI" w sekcji Cel i tryb?', answer: 'To silnik sztucznej inteligencji generujacy listing. Domyslnie uzywamy modelu Standardowego — jest wliczony w subskrypcje. Jesli chcesz lepszej jakosci, mozesz wybrac Ultra lub Premium (wymagaja Twojego klucza API). Klucz zapisujesz w Ustawienia → Model AI.' },
          { question: 'Jaka jest roznica miedzy modelami AI?', answer: 'Standardowy: w cenie subskrypcji, dobra jakosc, najszybszy. Zaawansowany: najwyzsza jakosc, bez limitow. Turbo: szybki i precyzyjny (wymaga klucza). Ultra: najlepsza jakosc tekstu (wymaga klucza). Premium: wszechstronny (wymaga klucza). Jesli nie wiesz co wybrac — zostaw Standardowy, jest wystarczajaco dobry.' },
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
