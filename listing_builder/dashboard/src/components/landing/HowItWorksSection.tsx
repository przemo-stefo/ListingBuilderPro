// src/components/landing/HowItWorksSection.tsx
// Purpose: 4-step process cards showing the product workflow
// NOT for: Feature details or pricing

'use client';

import { motion } from 'framer-motion';
import { ScanSearch, Brain, Shield, Zap } from 'lucide-react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { steps } from '@/lib/landing-data';

const iconMap: Record<string, React.ElementType> = {
  ScanSearch, Brain, Shield, Zap,
};

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="bg-[#121212] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="text-center"
        >
          <span className="text-sm font-medium tracking-wider text-green-500">HOW IT WORKS</span>
          <h2 className="mt-3 text-3xl font-bold text-white sm:text-4xl">
            From <span className="text-green-500">Reactive</span> to Proactive
          </h2>
        </motion.div>

        {/* Step cards - 2x2 grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-2"
        >
          {steps.map((step) => {
            const Icon = iconMap[step.icon];
            return (
              <motion.div
                key={step.number}
                variants={staggerItem}
                className="rounded-xl border border-border bg-[#1A1A1A] p-6"
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-green-500/10">
                    <Icon className="h-6 w-6 text-green-500" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-green-500">STEP {step.number}</span>
                    <h3 className="mt-1 text-lg font-semibold text-white">{step.title}</h3>
                    <p className="mt-2 text-sm text-neutral-400">{step.description}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
