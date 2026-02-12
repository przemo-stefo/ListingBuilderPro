// frontend/src/app/compliance/components/AkademiaTab.tsx
// Purpose: Akademia Marketplace landing — features overview + open in new tab
// NOT for: RSS feeds (those are in NewsTab) or file upload (UploadTab)

'use client'

import {
  GraduationCap,
  ExternalLink,
  BookOpen,
  MessageCircleQuestion,
  Newspaper,
  Shield,
  TrendingUp,
  Users,
} from 'lucide-react'

const AKADEMIA_URL = 'https://akademia-marketplace.pages.dev'

const FEATURES = [
  {
    icon: BookOpen,
    title: 'Baza Wiedzy',
    desc: 'Artykuły i przewodniki o sprzedaży na marketplace — Amazon, Allegro, eBay, Kaufland',
    color: 'text-blue-400 bg-blue-500/10',
  },
  {
    icon: MessageCircleQuestion,
    title: 'Q&A dla Sprzedawców',
    desc: 'Zadawaj pytania i otrzymuj odpowiedzi od ekspertów e-commerce',
    color: 'text-green-400 bg-green-500/10',
  },
  {
    icon: Newspaper,
    title: 'Aktualności',
    desc: 'Najnowsze zmiany w regulaminach, opłatach i politykach marketplace',
    color: 'text-orange-400 bg-orange-500/10',
  },
  {
    icon: Shield,
    title: 'Compliance',
    desc: 'Wymogi prawne — EPR, GPSR, CE, WEEE — dla sprzedawców cross-border',
    color: 'text-red-400 bg-red-500/10',
  },
  {
    icon: TrendingUp,
    title: 'Strategie Sprzedaży',
    desc: 'Optymalizacja listingów, PPC, Buy Box, pozycjonowanie produktów',
    color: 'text-purple-400 bg-purple-500/10',
  },
  {
    icon: Users,
    title: 'Społeczność',
    desc: 'Dołącz do społeczności sprzedawców — dziel się doświadczeniem i ucz od innych',
    color: 'text-cyan-400 bg-cyan-500/10',
  },
]

export default function AkademiaTab() {
  return (
    <div className="space-y-6">
      {/* Hero card */}
      <div className="relative overflow-hidden rounded-xl border border-gray-800 bg-gradient-to-br from-[#1A1A1A] to-[#121212] p-8">
        <div className="relative z-10 flex flex-col items-center text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 mb-4">
            <GraduationCap className="h-8 w-8 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Akademia Marketplace
          </h2>
          <p className="max-w-md text-gray-400 mb-6">
            Kompletna baza wiedzy dla sprzedawców. Artykuły, Q&A, aktualności
            i przewodniki o compliance na marketplace.
          </p>
          <a
            href={AKADEMIA_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            Otwórz Akademię
          </a>
        </div>
        {/* WHY: Decorative gradient blur in background */}
        <div className="absolute -right-20 -top-20 h-60 w-60 rounded-full bg-blue-500/5 blur-3xl" />
        <div className="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-blue-500/5 blur-3xl" />
      </div>

      {/* Feature grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5 transition-colors hover:border-gray-700"
          >
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${f.color} mb-3`}>
              <f.icon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">{f.title}</h3>
            <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="flex items-center justify-center rounded-xl border border-dashed border-gray-700 bg-[#1A1A1A]/50 p-6">
        <div className="text-center">
          <p className="text-sm text-gray-400 mb-3">
            Akademia otwiera się w nowej karcie dla pełnego doświadczenia
          </p>
          <a
            href={AKADEMIA_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-[#121212] px-4 py-2 text-sm text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
          >
            <GraduationCap className="h-4 w-4" />
            akademia-marketplace.pages.dev
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </div>
  )
}
