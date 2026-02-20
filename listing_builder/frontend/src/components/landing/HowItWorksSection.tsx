// frontend/src/components/landing/HowItWorksSection.tsx
// Purpose: 4-step grid showing product workflow (mirrors reference 2x2 layout)
// NOT for: Feature details (that's FeaturesSection)

'use client'

import { motion } from 'framer-motion'
import { Upload, Sparkles, RefreshCw, Rocket } from 'lucide-react'
import { MarketplaceLogos } from './MarketplaceLogos'

const STEPS = [
  {
    num: '01',
    icon: Upload,
    title: 'Importuj produkt',
    desc: 'Wklej URL z marketplace, prześlij CSV lub dodaj dane ręcznie. System automatycznie pobierze tytuł, opis i atrybuty.',
  },
  {
    num: '02',
    icon: Sparkles,
    title: 'AI optymalizuje',
    desc: 'Sztuczna inteligencja analizuje Twój listing i generuje zoptymalizowane tytuły, bullet pointy, opisy i słowa kluczowe.',
  },
  {
    num: '03',
    icon: RefreshCw,
    title: 'Konwertuj na inne platformy',
    desc: 'Jednym kliknięciem przenieś ofertę z Amazon na Allegro, eBay czy Kaufland. AI dostosowuje język i format.',
  },
  {
    num: '04',
    icon: Rocket,
    title: 'Eksportuj i publikuj',
    desc: 'Skopiuj gotową ofertę lub pobierz CSV. Twoje zoptymalizowane listingi są gotowe do publikacji.',
  },
]

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 px-6">
      <div className="mx-auto max-w-5xl">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Jak to działa</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Od surowego listingu do{' '}
            <span className="text-emerald-400">zoptymalizowanej oferty</span>
          </h2>
          <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
            AI analizuje, optymalizuje i konwertuje — Ty tylko publikujesz gotową ofertę.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {STEPS.map((step, i) => (
            <motion.div key={step.num}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="rounded-xl border border-gray-800 bg-[#0F1419]/60 p-6"
            >
              <div className="flex items-center gap-3 mb-3">
                <step.icon className="h-5 w-5 text-emerald-400" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">Krok {step.num}</span>
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{step.desc}</p>
            </motion.div>
          ))}
        </div>

        <MarketplaceLogos label="Obsługiwane platformy" className="mt-14" />
      </div>
    </section>
  )
}
