// src/components/landing/PricingSection.tsx
// Purpose: 3 pricing tiers - Starter / Pro (popular) / Agency
// NOT for: Feature details or comparison table

'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Check } from 'lucide-react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { pricingTiers } from '@/lib/landing-data';

export function PricingSection() {
  return (
    <section id="pricing" className="bg-[#121212] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="text-center"
        >
          <span className="text-sm font-medium tracking-wider text-green-500">PRICING</span>
          <h2 className="mt-3 text-3xl font-bold text-white sm:text-4xl">
            Simple, Transparent{' '}
            <span className="text-green-500">Pricing</span>
          </h2>
          <p className="mt-4 text-neutral-400">
            Start with a 14-day free trial. No credit card required. Cancel anytime.
          </p>
        </motion.div>

        {/* Pricing cards */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3"
        >
          {pricingTiers.map((tier) => (
            <motion.div
              key={tier.name}
              variants={staggerItem}
              className={`relative rounded-xl border p-6 ${
                tier.popular
                  ? 'border-green-500/50 bg-[#1A1A1A]'
                  : 'border-border bg-[#1A1A1A]'
              }`}
            >
              {/* Popular badge */}
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-green-500 px-3 py-1 text-xs font-medium text-black">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center">
                <h3 className="text-xl font-semibold text-white">{tier.name}</h3>
                <p className="mt-1 text-sm text-neutral-500">{tier.subtitle}</p>
                <div className="mt-6">
                  <span className="text-4xl font-bold text-white">&euro;{tier.price}</span>
                  <span className="text-neutral-500"> /month</span>
                </div>
              </div>

              {/* Features list */}
              <ul className="mt-8 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-neutral-300">
                    <Check className="h-4 w-4 shrink-0 text-green-400" />
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA button */}
              <a
                href="#"
                className={`mt-8 flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                  tier.popular
                    ? 'bg-green-500 text-black hover:bg-green-400'
                    : 'border border-border bg-[#121212] text-white hover:bg-[#1A1A1A]'
                }`}
              >
                {tier.cta} <ArrowRight className="h-4 w-4" />
              </a>
            </motion.div>
          ))}
        </motion.div>

        {/* Volume pricing note */}
        <motion.p
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-8 text-center text-sm text-neutral-500"
        >
          Need custom volume pricing?{' '}
          <a href="#" className="text-green-400 underline hover:text-green-300">
            Contact our sales team
          </a>
        </motion.p>
      </div>
    </section>
  );
}
