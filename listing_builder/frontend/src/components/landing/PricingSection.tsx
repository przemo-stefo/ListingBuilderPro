// frontend/src/components/landing/PricingSection.tsx
// Purpose: Pricing cards — Free vs Premium comparison with section label
// NOT for: Stripe checkout logic (that's /payment/ pages)

'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Check, ArrowRight } from 'lucide-react'

const FREE_FEATURES = [
  '3 optymalizacje dziennie',
  'Amazon marketplace',
  'Optymalizator AI (podstawowy)',
  'Import z URL',
]

const PREMIUM_FEATURES = [
  'Nieograniczone optymalizacje',
  'Wszystkie marketplace (Amazon, Allegro, eBay, Kaufland, Temu, AliExpress)',
  'Pełny optymalizator AI (7 modułów)',
  'Konwerter ofert między platformami',
  'Ekspert AI z bazą wiedzy',
  'Badanie rynku (10 skilli AI)',
  'Import CSV + eksport',
  'Compliance Guard',
  'Priorytetowe wsparcie',
]

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 px-6">
      <div className="mx-auto max-w-4xl">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Cennik</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Prosty, przejrzysty{' '}
            <span className="text-emerald-400">cennik</span>
          </h2>
          <p className="mt-4 text-gray-400">Zacznij za darmo. Przejdź na Premium gdy będziesz gotowy.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free tier */}
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.4 }}
            className="rounded-xl border border-gray-800 bg-[#0F1419]/60 p-8"
          >
            <h3 className="text-lg font-semibold text-white">Free</h3>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white">0 zł</span>
              <span className="text-sm text-gray-500">/mies</span>
            </div>
            <p className="mt-3 text-sm text-gray-400">Na start — poznaj narzędzie</p>

            <ul className="mt-8 space-y-3">
              {FREE_FEATURES.map(feat => (
                <li key={feat} className="flex items-start gap-3 text-sm text-gray-400">
                  <Check className="h-4 w-4 shrink-0 text-gray-600 mt-0.5" />
                  {feat}
                </li>
              ))}
            </ul>

            <Link href="/login"
              className="mt-8 flex items-center justify-center gap-2 w-full border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white font-medium py-3 rounded-lg transition-colors text-sm">
              Zacznij za darmo
            </Link>
          </motion.div>

          {/* Premium tier */}
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.4, delay: 0.1 }}
            className="relative rounded-xl border border-emerald-500/30 bg-[#0F1419]/60 p-8"
          >
            <div className="absolute -top-3 left-6 inline-flex items-center rounded-full bg-emerald-500 px-3 py-1">
              <span className="text-xs font-semibold text-white">Najpopularniejszy</span>
            </div>

            <h3 className="text-lg font-semibold text-white">Premium</h3>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white">49 zł</span>
              <span className="text-sm text-gray-500">/mies</span>
            </div>
            <p className="mt-3 text-sm text-gray-400">Pełna moc AI dla Twojego biznesu</p>

            <ul className="mt-8 space-y-3">
              {PREMIUM_FEATURES.map(feat => (
                <li key={feat} className="flex items-start gap-3 text-sm text-gray-300">
                  <Check className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
                  {feat}
                </li>
              ))}
            </ul>

            <Link href="/login"
              className="mt-8 flex items-center justify-center gap-2 w-full bg-emerald-500 hover:bg-emerald-400 text-white font-semibold py-3 rounded-lg transition-colors text-sm">
              Wykup Premium <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
