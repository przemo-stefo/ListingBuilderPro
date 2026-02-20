// frontend/src/components/landing/FeaturesSection.tsx
// Purpose: 6-card feature grid with category badges (mirrors reference layout)
// NOT for: Pricing or how-it-works (separate sections)

'use client'

import { motion } from 'framer-motion'
import { Sparkles, RefreshCw, MessageSquare, BarChart3, ShieldCheck, ArrowDownUp } from 'lucide-react'

const FEATURES = [
  {
    icon: Sparkles,
    badge: 'Core',
    title: 'Optymalizator AI',
    desc: 'Tytuły, bullet pointy, opisy i backend keywords — generowane przez AI w sekundach, nie godzinach.',
  },
  {
    icon: RefreshCw,
    badge: 'Konwersja',
    title: 'Konwerter Ofert',
    desc: 'Przenieś ofertę z Amazon na Allegro, eBay czy Kaufland jednym kliknięciem. AI dostosowuje język i format.',
  },
  {
    icon: MessageSquare,
    badge: 'Wiedza',
    title: 'Ekspert AI',
    desc: 'Zadaj pytanie o marketplace i otrzymaj odpowiedź opartą na bazie wiedzy od top sprzedawców.',
  },
  {
    icon: BarChart3,
    badge: 'Analityka',
    title: 'Badanie Rynku',
    desc: 'ICP, brief reklamowy, analiza grupy docelowej — 10 skilli AI do budowania przewagi konkurencyjnej.',
  },
  {
    icon: ShieldCheck,
    badge: 'Compliance',
    title: 'Compliance Guard',
    desc: 'Automatyczne sprawdzanie zgodności ofert z regulaminem marketplace. Zero ryzyka blokady konta.',
  },
  {
    icon: ArrowDownUp,
    badge: 'Import/Export',
    title: 'Import & Eksport',
    desc: 'Importuj produkty z marketplace lub CSV. Eksportuj zoptymalizowane oferty gotowe do publikacji.',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-6">
      <div className="mx-auto max-w-5xl">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Funkcje</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Wszystko czego potrzebujesz do{' '}
            <span className="text-emerald-400">sprzedaży online</span>
          </h2>
          <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
            Jedno narzędzie zamiast dziesięciu. Optymalizuj, konwertuj i analizuj swoje oferty z pomocą AI.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((feat, i) => (
            <motion.div key={feat.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="rounded-xl border border-gray-800 bg-[#0F1419]/60 p-6 hover:border-emerald-500/30 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <feat.icon className="h-5 w-5 text-emerald-400" />
                </div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full">
                  {feat.badge}
                </span>
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{feat.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
