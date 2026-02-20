// frontend/src/components/landing/ProblemSection.tsx
// Purpose: Problem section — why sellers need AI optimization (red accent cards)
// NOT for: Solutions/features (that's FeaturesSection)

'use client'

import { motion } from 'framer-motion'
import { EyeOff, TrendingDown, Clock, DollarSign } from 'lucide-react'
import { MarketplaceLogos } from './MarketplaceLogos'

const PROBLEMS = [
  { icon: EyeOff, title: 'Słaba widoczność', desc: 'Niezoptymalizowane tytuły i opisy obniżają pozycję w wynikach wyszukiwania.' },
  { icon: TrendingDown, title: 'Spadek sprzedaży', desc: 'Bez odpowiednich słów kluczowych kupujący nie znajdują Twojego produktu.' },
  { icon: Clock, title: 'Stracony czas', desc: 'Ręczne pisanie ofert na 4 marketplace zajmuje godziny zamiast minut.' },
  { icon: DollarSign, title: 'Wyższe koszty PPC', desc: 'Słabe listingi oznaczają niższy Quality Score i droższe reklamy.' },
]

export function ProblemSection() {
  return (
    <section className="py-24 px-6">
      <div className="mx-auto max-w-5xl">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-red-400">Problem</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Marketplace nie czeka.{' '}
            <span className="text-red-400">Twoja konkurencja też nie.</span>
          </h2>
          <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
            Sprzedawcy, którzy nie optymalizują swoich ofert, tracą pozycje na rzecz tych, którzy to robią.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {PROBLEMS.map((p, i) => (
            <motion.div key={p.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="rounded-xl border border-red-500/10 bg-red-500/[0.03] p-5 flex items-start gap-4"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-500/10 border border-red-500/20">
                <p.icon className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white mb-1">{p.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{p.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <p className="text-center mt-10 text-sm text-gray-500">
          Dzisiejsza optymalizacja jest <span className="font-semibold text-white">reaktywna</span>. Dowiadujesz się, gdy jest za późno.
        </p>

        <MarketplaceLogos label="Dotyczy platform" className="mt-12" />
      </div>
    </section>
  )
}
