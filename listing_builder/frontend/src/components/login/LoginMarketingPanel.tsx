// frontend/src/components/login/LoginMarketingPanel.tsx
// Purpose: Left marketing panel for login page — rotating slides with value props
// NOT for: Form logic or authentication (that's login/page.tsx)

'use client'

import { useState, useEffect } from 'react'
import { Sparkles, BarChart3, ShieldCheck, Zap } from 'lucide-react'

// WHY: Rotating marketing slides — shows different value props
const slides = [
  {
    icon: Sparkles,
    headline: 'Zoptymalizuj swoje oferty',
    accent: 'z pomocą AI',
    desc: 'Tytuły, opisy, słowa kluczowe — wszystko generowane przez AI, dostosowane do algorytmów marketplace.',
  },
  {
    icon: BarChart3,
    headline: 'Analizuj konkurencję',
    accent: 'i bądź o krok przed nią',
    desc: 'Badanie rynku, ICP, brief reklamowy — 10 skilli AI do budowania przewagi konkurencyjnej.',
  },
  {
    icon: ShieldCheck,
    headline: 'Sprzedawaj na wielu',
    accent: 'marketplace jednocześnie',
    desc: 'Amazon, Allegro, eBay, Kaufland — konwertuj oferty między platformami jednym kliknięciem.',
  },
  {
    icon: Zap,
    headline: 'Ekspert AI odpowiada',
    accent: 'na Twoje pytania 24/7',
    desc: 'Baza wiedzy od top sprzedawców. Zadaj pytanie i otrzymaj konkretną odpowiedź opartą na danych.',
  },
]

export function LoginMarketingPanel() {
  const [activeSlide, setActiveSlide] = useState(0)

  // WHY: Auto-rotate slides every 5s
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide(prev => (prev + 1) % slides.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  const slide = slides[activeSlide]
  const SlideIcon = slide.icon

  return (
    <div className="relative hidden lg:flex lg:w-1/2 flex-col justify-between p-12 overflow-hidden">
      {/* WHY: Subtle green radial glow — matches the screenshot aesthetic */}
      <div className="absolute inset-0 bg-[#0A0A0A]" />
      <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-emerald-500/8 blur-3xl" />
      <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-emerald-500/5 blur-3xl" />

      <div className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="h-5 w-5 text-emerald-400" />
          </div>
          <span className="text-lg font-semibold text-white">OctoHelper</span>
        </div>
      </div>

      <div className="relative z-10 space-y-6">
        <div className="flex items-center gap-3 mb-8">
          <SlideIcon className="h-8 w-8 text-emerald-400" />
        </div>
        <h2 className="text-4xl font-bold leading-tight text-white">
          {slide.headline}{' '}
          <span className="text-emerald-400">{slide.accent}</span>
        </h2>
        <p className="text-lg text-gray-400 max-w-md leading-relaxed">
          {slide.desc}
        </p>
      </div>

      <div className="relative z-10 flex items-center gap-3">
        <div className="flex gap-1.5">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setActiveSlide(i)}
              className={`h-2.5 w-2.5 rounded-full transition-all ${
                i === activeSlide
                  ? 'bg-emerald-400 w-6'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            />
          ))}
        </div>
        <span className="ml-4 text-sm text-gray-500">
          <span className="font-semibold text-white">500+</span> sprzedawców już korzysta
        </span>
      </div>
    </div>
  )
}
