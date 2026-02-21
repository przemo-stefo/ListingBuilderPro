// frontend/src/components/landing/ExpertsSection.tsx
// Purpose: Trust bar — "Tworzone przez ekspertów" with partner logos above FAQ
// NOT for: Marketplace logos (that's MarketplaceLogos)

'use client'

import { motion } from 'framer-motion'
import { Globe } from 'lucide-react'

const EXPERTS = [
  { name: 'OcotaIO', url: 'https://ocotaio.com' },
  { name: 'Otoneso', url: 'https://otoneso.pl' },
  { name: 'OctoSello', url: 'https://octosello.com' },
]

export function ExpertsSection() {
  return (
    <section className="py-16 px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="mx-auto max-w-3xl text-center"
      >
        <span className="text-xs font-medium uppercase tracking-widest text-gray-500">
          Tworzone przez ekspertów
        </span>
        <div className="mt-6 flex items-center justify-center gap-8 sm:gap-12 flex-wrap">
          {EXPERTS.map((expert) => (
            <a
              key={expert.name}
              href={expert.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Globe className="h-4 w-4 shrink-0" />
              <span className="text-sm font-semibold">{expert.name}</span>
            </a>
          ))}
        </div>
      </motion.div>
    </section>
  )
}
