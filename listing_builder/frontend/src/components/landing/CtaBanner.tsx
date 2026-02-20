// frontend/src/components/landing/CtaBanner.tsx
// Purpose: Final CTA banner before footer — push to sign up
// NOT for: Hero section (that's HeroSection)

import Link from 'next/link'
import { Sparkles, ArrowRight } from 'lucide-react'

export function CtaBanner() {
  return (
    <section className="py-24 px-6">
      <div className="mx-auto max-w-3xl text-center">
        <div className="flex justify-center mb-6">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="h-7 w-7 text-emerald-400" />
          </div>
        </div>

        <h2 className="text-3xl sm:text-4xl font-bold text-white">
          Nie trać klientów przez{' '}
          <span className="text-emerald-400">słabe oferty</span>
        </h2>
        <p className="mt-4 text-gray-400 max-w-xl mx-auto">
          Zacznij optymalizować swoje listingi już dziś. Wystarczy konto i 30 sekund.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/login"
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-8 py-3.5 rounded-lg transition-colors text-sm">
            Wypróbuj za darmo <ArrowRight className="h-4 w-4" />
          </Link>
          <a href="#features"
            className="flex items-center gap-2 border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-8 py-3.5 rounded-lg transition-colors text-sm">
            Zobacz funkcje
          </a>
        </div>

        <p className="mt-6 text-xs text-gray-600">
          Bez karty kredytowej &middot; Konfiguracja w 30 sekund
        </p>
      </div>
    </section>
  )
}
