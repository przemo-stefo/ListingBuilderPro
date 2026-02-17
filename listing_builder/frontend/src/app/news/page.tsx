// frontend/src/app/news/page.tsx
// Purpose: Standalone page for marketplace news aggregator (RSS feeds)
// NOT for: Compliance checks or alert management

'use client'

import NewsTab from '../compliance/components/NewsTab'
import { FaqSection } from '@/components/ui/FaqSection'

const NEWS_FAQ = [
  { question: 'Skad pochodza nowosci?', answer: 'System agreguje wiadomosci z oficjalnych kanalow marketplace (Amazon Seller Central, eBay Announcements, Allegro dla Sprzedajacych) oraz branżowych zrodel o e-commerce.' },
  { question: 'Jak czesto sa aktualizowane?', answer: 'Nowosci sa pobierane automatycznie co kilka godzin z kanalow RSS. Najnowsze wiadomosci pojawiaja sie na gorze listy.' },
  { question: 'Dlaczego warto sledzic nowosci?', answer: 'Zmiany regulacji, nowe opłaty, aktualizacje algorytmow — wszystko to wplywa na Twoja sprzedaz. Wczesne reagowanie na zmiany daje przewage nad konkurencja.' },
]

export default function NewsPage() {
  return (
    <div className="space-y-6">
      <NewsTab />
      <FaqSection
        title="Najczesciej zadawane pytania"
        subtitle="Nowosci marketplace"
        items={NEWS_FAQ}
      />
    </div>
  )
}
