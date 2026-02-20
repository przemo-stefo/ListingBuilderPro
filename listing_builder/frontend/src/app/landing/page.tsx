// frontend/src/app/landing/page.tsx
// Purpose: Landing page shell — imports and composes all LP sections
// NOT for: Section content (each section is a separate component)

import type { Metadata } from 'next'
import { LandingNav } from '@/components/landing/LandingNav'
import { HeroSection } from '@/components/landing/HeroSection'
import { ProblemSection } from '@/components/landing/ProblemSection'
import { HowItWorksSection } from '@/components/landing/HowItWorksSection'
import { ShowcaseSection } from '@/components/landing/ShowcaseSection'
import { FeaturesSection } from '@/components/landing/FeaturesSection'
import { ComparisonSection } from '@/components/landing/ComparisonSection'
import { PricingSection } from '@/components/landing/PricingSection'
import { LandingFaqSection } from '@/components/landing/LandingFaqSection'
import { CtaBanner } from '@/components/landing/CtaBanner'
import { FooterSection } from '@/components/landing/FooterSection'

// WHY: SEO metadata — critical for a marketing landing page
export const metadata: Metadata = {
  title: 'OctoHelper — AI Marketplace Assistant | Optymalizuj oferty z AI',
  description: 'Optymalizuj oferty na Amazon, Allegro, eBay i Kaufland z pomocą AI. Generuj tytuły, opisy, słowa kluczowe. Konwertuj między platformami jednym kliknięciem.',
  openGraph: {
    title: 'OctoHelper — AI Marketplace Assistant',
    description: 'Optymalizuj oferty marketplace z pomocą AI. Amazon, Allegro, eBay, Kaufland.',
    type: 'website',
    url: 'https://panel.octohelper.com/landing',
  },
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      <LandingNav />
      <main>
        <HeroSection />
        <ProblemSection />
        <HowItWorksSection />
        <ShowcaseSection />
        <FeaturesSection />
        <ComparisonSection />
        <PricingSection />
        <LandingFaqSection />
        <CtaBanner />
      </main>
      <FooterSection />
    </div>
  )
}
