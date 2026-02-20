// frontend/src/components/landing/HeroSection.tsx
// Purpose: Hero section — headline, CTAs, dashboard preview widget
// NOT for: Navigation (that's LandingNav)

'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Play, TrendingUp, CheckCircle2, AlertTriangle, Clock } from 'lucide-react'

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-20 pb-16 px-6">
      {/* WHY: Emerald radial glows — matching reference aesthetic */}
      <div className="absolute -top-40 -right-40 h-[500px] w-[500px] rounded-full bg-emerald-500/8 blur-3xl" />
      <div className="absolute -bottom-40 -left-40 h-[400px] w-[400px] rounded-full bg-emerald-500/5 blur-3xl" />

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-4 py-1.5 mb-8">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">AI-Powered Marketplace Assistant</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight tracking-tight">
            Twoje oferty marketplace{' '}
            <span className="text-emerald-400">zoptymalizowane przez AI</span>
          </h1>

          <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            System AI do optymalizacji listingów na Amazon, Allegro, eBay i Kaufland.
            Lepsze tytuły, opisy i słowa kluczowe — zanim konkurencja Cię wyprzedzi.
          </p>
        </motion.div>

        {/* CTAs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/login"
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-8 py-3.5 rounded-lg transition-colors text-sm">
            Wypróbuj za darmo <ArrowRight className="h-4 w-4" />
          </Link>
          <a href="#how-it-works"
            className="flex items-center gap-2 border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-8 py-3.5 rounded-lg transition-colors text-sm">
            <Play className="h-4 w-4" /> Zobacz jak działa
          </a>
        </motion.div>

        {/* WHY: Dashboard preview widget — mirrors reference "Compliance Radar" pattern */}
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-16 mx-auto max-w-xl">
          <div className="rounded-xl border border-gray-800 bg-[#0F1419]/80 backdrop-blur-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span className="text-sm font-semibold text-white">Optymalizator AI</span>
              <span className="ml-auto text-[10px] text-gray-500 uppercase tracking-wider">Live preview</span>
            </div>
            <div className="space-y-2.5">
              {[
                { icon: CheckCircle2, color: 'text-emerald-400', text: 'Tytuł — Zoptymalizowany, +23% widoczności' },
                { icon: AlertTriangle, color: 'text-amber-400', text: 'Backend Keywords — 3 słowa do dodania' },
                { icon: Clock, color: 'text-gray-500', text: 'Opis — Oczekuje na optymalizację' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 rounded-lg bg-[#1A1F26]/60 px-4 py-2.5">
                  <item.icon className={`h-4 w-4 shrink-0 ${item.color}`} />
                  <span className="text-xs text-gray-300">{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
