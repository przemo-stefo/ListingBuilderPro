// frontend/src/app/pricing/page.tsx
// Purpose: Standalone pricing page — accessible without login
// NOT for: Stripe checkout (that's /payment/) or landing page (that's /landing)

import { PricingSection } from '@/components/landing/PricingSection'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export const metadata = {
  title: 'Cennik — OctoHelper',
  description: 'Prosty cennik: Free (0 zł) i Premium (19,99 zł/mies). Zacznij za darmo.',
}

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      <div className="mx-auto max-w-4xl px-6 pt-8">
        <Link
          href="/landing"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Strona główna
        </Link>
      </div>
      <PricingSection />
    </div>
  )
}
