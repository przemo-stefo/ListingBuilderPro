// frontend/src/components/landing/ComparisonSection.tsx
// Purpose: Comparison table — OctoHelper AI vs manual optimization
// NOT for: Feature details (that's FeaturesSection)

'use client'

import { motion } from 'framer-motion'
import { Check, X } from 'lucide-react'

const ROWS = [
  { aspect: 'Szybkość', manual: 'Godziny na jeden listing', ai: 'Sekundy na jeden listing' },
  { aspect: 'Jakość', manual: 'Zależna od doświadczenia', ai: 'Bazuje na danych top sprzedawców' },
  { aspect: 'Marketplace', manual: 'Jeden marketplace na raz', ai: '6 platform jednocześnie' },
  { aspect: 'SEO Keywords', manual: 'Ręczny research', ai: 'Automatyczna analiza i rozmieszczenie' },
  { aspect: 'Konwersja', manual: 'Przepisywanie od zera', ai: 'Jednym kliknięciem między platformami' },
  { aspect: 'Compliance', manual: 'Ręczne sprawdzanie regulaminów', ai: 'Automatyczny Compliance Guard' },
  { aspect: 'Skalowalność', manual: 'Nie skaluje się', ai: 'Nieograniczona liczba produktów' },
  { aspect: 'Koszt', manual: 'Copywriter od 50 zł/listing', ai: 'Od 0 zł — free tier dostępny' },
]

export function ComparisonSection() {
  return (
    <section className="py-24 px-6">
      <div className="mx-auto max-w-3xl">
        <div className="text-center mb-16">
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Dlaczego my</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
            Koniec z ręcznym pisaniem{' '}
            <span className="text-emerald-400">ofert</span>
          </h2>
          <p className="mt-4 text-gray-400 max-w-xl mx-auto">
            OctoHelper zastępuje godziny ręcznej pracy minutami z AI.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="rounded-xl border border-gray-800 bg-[#0F1419]/60 overflow-x-auto"
        >
          {/* WHY: min-w prevents column collapse on mobile, overflow-x-auto on parent scrolls */}
          <table className="w-full text-sm min-w-[540px]">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-6 py-4 text-gray-500 font-medium">Aspekt</th>
                <th className="text-left px-6 py-4 text-gray-500 font-medium">Ręcznie</th>
                <th className="text-left px-6 py-4 text-emerald-400 font-medium">OctoHelper AI</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, i) => (
                <tr key={row.aspect} className={i < ROWS.length - 1 ? 'border-b border-gray-800/50' : ''}>
                  <td className="px-6 py-4 font-medium text-white">{row.aspect}</td>
                  <td className="px-6 py-4 text-gray-500">
                    <span className="flex items-center gap-2">
                      <X className="h-3.5 w-3.5 text-red-400 shrink-0" /> {row.manual}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-300">
                    <span className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" /> {row.ai}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </div>
    </section>
  )
}
