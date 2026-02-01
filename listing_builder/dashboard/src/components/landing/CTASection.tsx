// src/components/landing/CTASection.tsx
// Purpose: Final call-to-action section before footer
// NOT for: Hero or pricing content

'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Shield } from 'lucide-react';
import { fadeInUp } from '@/lib/animations';

export function CTASection() {
  return (
    <section className="relative overflow-hidden bg-[#1A1A1A] px-4 py-24 sm:px-6 lg:px-8">
      {/* Subtle gradient glow */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(34,197,94,0.06)_0%,transparent_70%)]" />

      <div className="relative mx-auto max-w-3xl text-center">
        <motion.div variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
          <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-green-500/10">
            <Shield className="h-7 w-7 text-green-500" />
          </div>

          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Don&apos;t Wait for the{' '}
            <span className="text-green-500">Blocking Email</span>
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Start your free compliance analysis today. Know your risks across
            Amazon, eBay, and Kaufland in minutes.
          </p>

          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-lg bg-green-500 px-6 py-3 text-sm font-medium text-black transition-colors hover:bg-green-400"
            >
              Start Free 14-Day Trial <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="#"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-[#121212] px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-[#1A1A1A]"
            >
              Schedule Demo
            </a>
          </div>

          <p className="mt-4 text-sm text-neutral-600">
            No credit card required &middot; Setup in under 5 minutes
          </p>
        </motion.div>
      </div>
    </section>
  );
}
