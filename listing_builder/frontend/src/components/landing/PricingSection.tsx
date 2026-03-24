// frontend/src/components/landing/PricingSection.tsx
// Purpose: Single pricing card — 19 PLN/mies, no free tier (Mateusz 24.03)
// NOT for: Stripe checkout logic (that's /payment/ pages)

'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Check, ArrowRight } from 'lucide-react'

const FEATURES = [
  'Optymalizator AI — bez limitów, wszystkie marketplace',
  'Import produktów z URL, CSV i Allegro',
  'Konwerter ofert między platformami',
  'Listing Score — ocena listingu AI',
  'Walidator Produktu — analiza potencjału sprzedażowego',
  'Ekspert Kaufland — AI chatbot z bazą wiedzy',
  'Auto-Atrybuty — generowanie atrybutów z AI',
  'Priorytetowe wsparcie',
]

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 px-6">
      <div className="mx-auto max-w-lg">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Cennik</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Jeden plan, pełne{' '}
            <span className="text-emerald-400">możliwości</span>
          </h2>
          <p className="mt-4 text-gray-400">Wszystkie narzędzia AI w jednej subskrypcji.</p>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.4 }}
          className="relative rounded-xl border border-emerald-500/30 bg-[#0F1419]/60 p-8"
        >
          <div className="absolute -top-3 left-6 inline-flex items-center rounded-full bg-emerald-500 px-3 py-1">
            <span className="text-xs font-semibold text-white">Pełny dostęp</span>
          </div>

          <h3 className="text-lg font-semibold text-white">OctoHelper</h3>
          <div className="mt-4 flex items-baseline gap-1">
            <span className="text-4xl font-bold text-white">19,00 zł</span>
            <span className="text-sm text-gray-500">/mies</span>
          </div>
          <p className="mt-3 text-sm text-gray-400">Pełna moc AI dla Twojego biznesu</p>

          <ul className="mt-8 space-y-3">
            {FEATURES.map(feat => (
              <li key={feat} className="flex items-start gap-3 text-sm text-gray-300">
                <Check className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
                {feat}
              </li>
            ))}
          </ul>

          <Link href="/login"
            className="mt-8 flex items-center justify-center gap-2 w-full bg-emerald-500 hover:bg-emerald-400 text-white font-semibold py-3 rounded-lg transition-colors text-sm">
            Zacznij teraz <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
