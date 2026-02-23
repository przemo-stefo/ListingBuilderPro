// frontend/src/components/login/LoginMarketingPanel.tsx
// Purpose: Left marketing panel for login page — explains what OctoHelper does
// NOT for: Form logic or authentication (that's login/page.tsx)

import { Sparkles, PenTool, Globe, Upload, Brain, Search, Check } from 'lucide-react'

// WHY: Static feature list — clear "what does this tool do" before login
const features = [
  {
    icon: PenTool,
    title: 'Optymalizacja listingów AI',
    desc: 'Tytuły, bullet points, opisy i backend keywords — generowane przez AI pod algorytmy marketplace.',
  },
  {
    icon: Globe,
    title: '5 marketplace w jednym panelu',
    desc: 'Amazon, Allegro, eBay, Kaufland, BOL.com — twórz i konwertuj oferty między platformami.',
  },
  {
    icon: Upload,
    title: 'Szybki import produktów',
    desc: 'Wrzuć CSV, wklej URL oferty lub zaimportuj prosto z konta Allegro.',
  },
  {
    icon: Brain,
    title: 'Ekspert AI — chatbot e-commerce',
    desc: 'Zadaj pytanie o słowa kluczowe, PPC, ranking — AI odpowie na bazie 10 000+ fragmentów wiedzy.',
  },
  {
    icon: Search,
    title: 'Badanie rynku i konkurencji',
    desc: 'Analiza grupy docelowej, persony kupujących, brief reklamowy — 10 narzędzi badawczych.',
  },
]

export function LoginMarketingPanel() {
  return (
    <div className="relative hidden lg:flex lg:w-1/2 flex-col justify-between p-12 overflow-hidden">
      <div className="absolute inset-0 bg-[#0A0A0A]" />
      <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-emerald-500/8 blur-3xl" />
      <div className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-emerald-500/5 blur-3xl" />

      {/* Logo */}
      <div className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="h-5 w-5 text-emerald-400" />
          </div>
          <span className="text-lg font-semibold text-white">OctoHelper</span>
        </div>
      </div>

      {/* WHY: Static feature list — user sees exactly what the tool does before signing up */}
      <div className="relative z-10 space-y-5">
        <div>
          <h2 className="text-3xl font-bold leading-tight text-white">
            Twoje oferty,{' '}
            <span className="text-emerald-400">zoptymalizowane AI</span>
          </h2>
          <p className="mt-2 text-gray-400 max-w-sm">
            Panel do tworzenia i optymalizacji listingów na największych marketplace w Europie.
          </p>
        </div>

        <div className="space-y-3">
          {features.map((f) => {
            const Icon = f.icon
            return (
              <div key={f.title} className="flex gap-3 rounded-xl border border-gray-800/60 bg-gray-900/30 p-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                  <Icon className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white">{f.title}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* WHY: Free tier highlight — lowers signup friction */}
      <div className="relative z-10 flex items-center gap-2 text-sm text-gray-500">
        <Check className="h-4 w-4 text-emerald-500" />
        <span>3 darmowe optymalizacje dziennie — bez karty kredytowej</span>
      </div>
    </div>
  )
}
