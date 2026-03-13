// frontend/src/app/video-gen/components/VideoInfoSections.tsx
// Purpose: Static info sections — how it works, info cards, use cases, FAQ
// NOT for: Interactive state or video generation logic (that's page.tsx)

import { Zap, Clock, Video, Sparkles, CheckCircle2 } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const STEPS = [
  { num: 1, color: 'blue', title: 'Wgraj zdjecie', desc: 'Wklej link do produktu z Amazon, Allegro, eBay lub innego marketplace — albo wgraj zdjecie recznie (PNG, JPG, WebP, max 10 MB).' },
  { num: 2, color: 'cyan', title: 'Opisz ruch', desc: 'Wybierz predefiniowany styl lub wpisz wlasny opis ruchu. Np. "obrot produktu, swiatlo studyjne" lub "zoom, dramatyczne oswietlenie".' },
  { num: 3, color: 'green', title: 'AI generuje', desc: 'Zaawansowany model AI analizuje obraz i generuje 33 klatki plynnej animacji. Trwa to okolo 2-5 minut.' },
  { num: 4, color: 'yellow', title: 'Pobierz wideo', desc: 'Gotowe wideo w formacie WebP. Pobierz i uzyj na Amazon, Allegro, eBay, w reklamach lub social media.' },
] as const

const USE_CASES = [
  { title: 'Listingi na Amazon/Allegro', desc: 'Dynamiczne prezentacje produktow przyciagaja wiecej klikniec niz statyczne zdjecia. Amazon pozwala na wideo w galerii produktu.' },
  { title: 'Reklamy w social media', desc: 'Krotkie wideo produktowe do Facebook Ads, Instagram Reels, TikTok — bez koniecznosci nagrywania.' },
  { title: 'Prezentacje produktow', desc: 'Pokaz produkt w ruchu — obrot 360, zoom na detale, efekty swietlne. Idealny do stron produktowych i landing page.' },
  { title: 'Oszczednosc czasu i kosztow', desc: 'Zamiast organizowac sesje wideo z fotografem, wgraj jedno zdjecie i otrzymaj profesjonalne wideo w kilka minut.' },
]

const FAQ_ITEMS = [
  { question: 'Jak to dziala?', answer: 'Wklej link do produktu z Amazon, Allegro, eBay lub innego marketplace — system automatycznie pobierze zdjecie produktu. Mozesz tez wgrac wlasne zdjecie. Wybierz styl ruchu i kliknij "Generuj". AI tworzy plynna animacje z 33 klatek w 2-5 minut.' },
  { question: 'Jakie marketplace sa obslugiwane?', answer: 'Amazon (DE, US, UK, PL), Allegro, eBay, Kaufland, Rozetka, AliExpress i Temu. Wystarczy wkleic link do strony produktu — system sam znajdzie glowne zdjecie i wygeneruje wideo.' },
  { question: 'Jakie zdjecia daja najlepsze wyniki?', answer: 'Najlepsze wyniki daja zdjecia na bialym lub jednolitym tle, dobrze oswietlone, z produktem w centrum kadru. Rozdzielczosc co najmniej 800x800 px. Unikaj zdjec z wieloma przedmiotami lub skomplikowanym tlem.' },
  { question: 'Jakie formaty plikow sa obslugiwane?', answer: 'Na wejsciu: PNG, JPG, WebP (max 10 MB). Na wyjsciu: animowany WebP (33 klatki, 832x480 px, 16 fps). Format WebP jest obslugiwany przez Chrome, Firefox, Safari, Edge — i przez Amazon, Allegro, eBay.' },
  { question: 'Czy moge uzyc wideo na Amazon lub Allegro?', answer: 'Tak! Amazon pozwala na wideo w galerii produktu (A+ Content). Allegro rowniez obsluguje wideo w ofertach. Mozesz tez skonwertowac WebP na MP4 jesli marketplace wymaga innego formatu.' },
  { question: 'Ile trwa generowanie jednego wideo?', answer: 'Okolo 2-5 minut, w zaleznosci od obciazenia systemu. W tym czasie AI tworzy 33 klatki animacji na podstawie Twojego zdjecia i opisu ruchu.' },
  { question: 'Co jesli AI wygeneruje zly wynik?', answer: 'Zmien opis ruchu (prompt) i sprobuj ponownie. Rozne prompty daja rozne efekty — "rotation" da obrot, "zoom in" da przyblizenie, "floating" da efekt unoszenia sie. Mozesz tez uzyc predefiniowanych stylow.' },
  { question: 'Ile wideo moge wygenerowac?', answer: 'W planie Premium nie ma limitu. Jedyne ograniczenie to czas generowania (2-5 min na wideo). Jesli system jest zajety innym zadaniem, moze trzeba poczekac chwile dluzej.' },
  { question: 'Czy moje zdjecia sa bezpieczne?', answer: 'Tak. Zdjecia sa przetwarzane na dedykowanym serwerze i automatycznie usuwane po wygenerowaniu wideo. Nie sa przechowywane ani udostepniane osobom trzecim.' },
]

// WHY: Color mapping for step circles — Tailwind can't interpolate dynamic class names
const STEP_COLORS: Record<string, string> = {
  blue: 'bg-blue-500/20 text-blue-400',
  cyan: 'bg-cyan-500/20 text-cyan-400',
  green: 'bg-green-500/20 text-green-400',
  yellow: 'bg-yellow-500/20 text-yellow-400',
}

export function HowItWorks() {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
      <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <Zap className="h-5 w-5 text-yellow-400" />
        Jak to dziala — krok po kroku
      </h2>
      <div className="grid gap-4 md:grid-cols-4">
        {STEPS.map((step) => (
          <div key={step.num} className="relative">
            <div className="flex items-center gap-3 mb-2">
              <span className={`flex h-8 w-8 items-center justify-center rounded-full font-bold text-sm ${STEP_COLORS[step.color]}`}>
                {step.num}
              </span>
              <h3 className="font-semibold text-white">{step.title}</h3>
            </div>
            <p className="text-sm text-gray-400 ml-11">{step.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function InfoCards() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-5 w-5 text-cyan-400" />
          <p className="text-sm font-semibold text-white">Szybko</p>
        </div>
        <p className="text-3xl font-bold text-cyan-400">2-5 min</p>
        <p className="text-xs text-gray-500 mt-2">Wideo generowane jest automatycznie — wystarczy wgrac zdjecie i wybrac styl.</p>
      </div>
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <div className="flex items-center gap-2 mb-2">
          <Video className="h-5 w-5 text-green-400" />
          <p className="text-sm font-semibold text-white">Gotowe do uzycia</p>
        </div>
        <p className="text-3xl font-bold text-green-400">WebP</p>
        <p className="text-xs text-gray-500 mt-2">Animowany format obslugiwany przez Amazon, Allegro, eBay i wszystkie przegladarki.</p>
      </div>
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-5 w-5 text-blue-400" />
          <p className="text-sm font-semibold text-white">Wliczone w Premium</p>
        </div>
        <p className="text-3xl font-bold text-blue-400">Bez limitu</p>
        <p className="text-xs text-gray-500 mt-2">Generowanie wideo jest czescia planu Premium — bez dodatkowych oplat za pojedyncze wideo.</p>
      </div>
    </div>
  )
}

export function UseCases() {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-6">
      <h2 className="text-xl font-bold text-white mb-4">Do czego sluzy?</h2>
      <div className="grid gap-3 md:grid-cols-2">
        {USE_CASES.map((item) => (
          <div key={item.title} className="flex gap-3 p-3 rounded-lg bg-[#121212]">
            <CheckCircle2 className="h-5 w-5 text-green-400 mt-0.5 shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-white">{item.title}</h3>
              <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function VideoFaq() {
  return (
    <FaqSection
      title="FAQ — Generator wideo AI"
      subtitle="Pytania o generowanie wideo produktowych"
      items={FAQ_ITEMS}
    />
  )
}
