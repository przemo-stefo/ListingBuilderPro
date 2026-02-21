// frontend/src/components/landing/ShowcaseSection.tsx
// Purpose: Product showcase — floating UI cards mimicking the actual panel
// NOT for: Feature descriptions (that's FeaturesSection)

'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Sparkles, TrendingUp, ArrowRight } from 'lucide-react'

// WHY: Extracted so mobile and desktop can reuse the same card data
const BEFORE_TITLE = 'Butelka termiczna stal nierdzewna'
const AFTER_TITLE = 'Butelka Termiczna 750ml Stal Nierdzewna | Termos Sport BPA-Free Izolacja 24h'

export function ShowcaseSection() {
  return (
    <section className="py-24 px-6 overflow-hidden">
      <div className="mx-auto max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Left: text */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Zobacz w akcji</span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-white leading-tight">
            Automatyczna{' '}
            <span className="text-emerald-400">optymalizacja ofert</span>
          </h2>
          <p className="mt-6 text-gray-400 leading-relaxed">
            System AI analizuje Twoje listingi, identyfikuje słabe punkty i generuje zoptymalizowane treści — od tytułów i opisów po backend keywords. Wystarczy jedno kliknięcie, żeby podnieść widoczność oferty na marketplace.
          </p>
          <div className="mt-8 flex flex-col gap-3">
            {[
              'Tytuły zoptymalizowane pod algorytm wyszukiwania',
              'Bullet pointy z najważniejszymi słowami kluczowymi',
              'Backend keywords dopasowane do niszy',
            ].map((item) => (
              <div key={item} className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <span className="text-sm text-gray-300">{item}</span>
              </div>
            ))}
          </div>

          {/* WHY: Mobile-only stacked cards — desktop uses absolute-positioned floating layout */}
          <div className="mt-10 flex flex-col gap-4 lg:hidden">
            {/* Before/After title card */}
            <div className="rounded-xl border border-gray-700 bg-[#141A21]/90 p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-white uppercase tracking-wider">Optymalizacja tytułu</span>
              </div>
              <div className="space-y-2.5">
                <div className="flex items-start gap-2 rounded-lg bg-red-500/5 border border-red-500/10 px-3 py-2">
                  <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-gray-400 line-through">{BEFORE_TITLE}</p>
                </div>
                <div className="flex items-start gap-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-3 py-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-gray-300">{AFTER_TITLE}</p>
                </div>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-gray-700 bg-[#141A21]/90 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white">Pokrycie keywords</span>
                  <span className="text-xs font-bold text-emerald-400">97%</span>
                </div>
                <div className="h-2 rounded-full bg-gray-800">
                  <div className="h-2 rounded-full bg-emerald-500 w-[97%]" />
                </div>
              </div>
              <div className="rounded-xl border border-gray-700 bg-[#141A21]/90 p-4 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 shrink-0">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">23</p>
                  <p className="text-[10px] text-gray-500">zoptymalizowane</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: floating UI mockup (desktop only) */}
        <div className="relative h-[480px] hidden lg:block">
          {/* WHY: Glow behind cards — depth effect */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />

          {/* Card 1: Status notification */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="absolute top-0 right-0 w-72 rounded-xl border border-gray-700 bg-[#141A21]/90 backdrop-blur-sm p-4 shadow-2xl"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Zoptymalizowano 23 listingi</p>
                <p className="text-xs text-gray-500">Pokrycie keywords: 97%</p>
              </div>
            </div>
          </motion.div>

          {/* Card 2: Before/After title */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="absolute top-24 left-0 w-80 rounded-xl border border-gray-700 bg-[#141A21]/90 backdrop-blur-sm p-4 shadow-2xl"
          >
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-semibold text-white uppercase tracking-wider">Optymalizacja tytułu</span>
            </div>
            <div className="space-y-2.5">
              <div className="flex items-start gap-2 rounded-lg bg-red-500/5 border border-red-500/10 px-3 py-2">
                <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-400 line-through">{BEFORE_TITLE}</p>
              </div>
              <div className="flex items-start gap-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-3 py-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-300">{AFTER_TITLE}</p>
              </div>
            </div>
          </motion.div>

          {/* Card 3: AI sparkle icon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="absolute top-44 right-8 flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/30 bg-[#141A21]/90 backdrop-blur-sm shadow-2xl"
          >
            <Sparkles className="h-7 w-7 text-emerald-400" />
          </motion.div>

          {/* Card 4: Keyword coverage bar */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="absolute bottom-24 right-4 w-64 rounded-xl border border-gray-700 bg-[#141A21]/90 backdrop-blur-sm p-4 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Pokrycie keywords</span>
              <span className="text-xs font-bold text-emerald-400">97%</span>
            </div>
            <div className="h-2 rounded-full bg-gray-800">
              <div className="h-2 rounded-full bg-emerald-500 w-[97%]" />
            </div>
            <p className="mt-2 text-[10px] text-gray-500">3 keywords do dodania w backend</p>
          </motion.div>

          {/* Card 5: Recommendation */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="absolute bottom-0 left-4 w-72 rounded-xl border border-gray-700 bg-[#141A21]/90 backdrop-blur-sm p-4 shadow-2xl"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="h-6 w-6 rounded bg-emerald-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              </div>
              <span className="text-xs font-semibold text-white">Rekomendacja:</span>
            </div>
            <p className="text-xs text-gray-400 mb-3">
              Optymalizacja tytułów i opisów, uzupełnienie słów kluczowych w backend keywords.
            </p>
            <button className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors">
              Zaakceptuj zmiany <ArrowRight className="h-3 w-3" />
            </button>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
