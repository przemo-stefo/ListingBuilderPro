// frontend/src/components/landing/LandingFaqSection.tsx
// Purpose: FAQ accordion for landing page with section label
// NOT for: In-app FAQ (that's ui/FaqSection.tsx)

'use client'

import { FaqItem } from '@/components/ui/FaqSection'

const FAQ_ITEMS = [
  {
    question: 'Czy OctoHelper jest darmowy?',
    answer: 'Tak! Plan Free daje Ci 3 optymalizacje dziennie na platformie Amazon. Jeśli potrzebujesz więcej — plan Premium za 49 zł/mies odblokowuje nielimitowane optymalizacje i wszystkie marketplace.',
  },
  {
    question: 'Jakie marketplace są obsługiwane?',
    answer: 'Amazon, Allegro, eBay i Kaufland. Konwerter ofert pozwala przenosić listingi między tymi platformami jednym kliknięciem.',
  },
  {
    question: 'Jak działa optymalizacja AI?',
    answer: 'AI analizuje Twój listing i generuje zoptymalizowane wersje tytułu, bullet pointów, opisu i słów kluczowych. Wykorzystuje bazę wiedzy od top sprzedawców i najlepsze praktyki SEO marketplace.',
  },
  {
    question: 'Czy mogę importować istniejące produkty?',
    answer: 'Tak — wklej URL oferty z marketplace lub prześlij plik CSV. System automatycznie pobierze wszystkie dane produktu.',
  },
  {
    question: 'Czy moje dane są bezpieczne?',
    answer: 'Absolutnie. Dane przechowujemy w szyfrowanej bazie PostgreSQL. Nie udostępniamy ich osobom trzecim. Komunikacja z API jest zabezpieczona kluczem po stronie serwera.',
  },
  {
    question: 'Mogę anulować subskrypcję w każdej chwili?',
    answer: 'Tak, bez żadnych zobowiązań. Anuluj kiedy chcesz z poziomu ustawień konta. Po anulowaniu wrócisz do planu Free.',
  },
]

export function LandingFaqSection() {
  return (
    <section id="faq" className="py-24 px-6">
      <div className="mx-auto max-w-2xl">
        <div className="text-center mb-12">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">FAQ</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Często zadawane{' '}
            <span className="text-emerald-400">pytania</span>
          </h2>
        </div>

        <div className="space-y-3">
          {FAQ_ITEMS.map((item, i) => (
            <FaqItem key={i} question={item.question} answer={item.answer} />
          ))}
        </div>
      </div>
    </section>
  )
}
