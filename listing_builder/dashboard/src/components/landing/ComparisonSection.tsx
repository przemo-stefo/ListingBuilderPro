// src/components/landing/ComparisonSection.tsx
// Purpose: Traditional EPR vs AI Compliance Guard comparison table
// NOT for: Feature descriptions or pricing

'use client';

import { motion } from 'framer-motion';
import { X, Check } from 'lucide-react';
import { fadeInUp } from '@/lib/animations';
import { comparisonRows } from '@/lib/landing-data';

export function ComparisonSection() {
  return (
    <section className="bg-[#1A1A1A] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-12 text-center"
        >
          <span className="text-sm font-medium tracking-wider text-green-500">WHY US</span>
          <h2 className="mt-3 text-3xl font-bold text-white sm:text-4xl">
            We&apos;re Not Another{' '}
            <span className="text-green-500">EPR Provider</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-neutral-400">
            EPR providers help you register. We help you stay compliant and avoid blocks.
            We work above them, not instead of them.
          </p>
        </motion.div>

        {/* Table */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="overflow-hidden rounded-xl border border-border"
        >
          {/* Header row */}
          <div className="grid grid-cols-3 bg-[#121212] px-6 py-4 text-sm font-medium">
            <span className="text-neutral-400">Aspect</span>
            <span className="text-center text-neutral-400">Traditional EPR</span>
            <span className="text-center text-green-500">AI Compliance Guard</span>
          </div>

          {/* Data rows */}
          {comparisonRows.map((row, i) => (
            <div
              key={row.aspect}
              className={`grid grid-cols-3 px-6 py-4 text-sm ${
                i % 2 === 0 ? 'bg-[#1A1A1A]' : 'bg-[#161616]'
              }`}
            >
              <span className="font-medium text-white">{row.aspect}</span>
              <span className="flex items-center justify-center gap-2 text-neutral-400">
                <X className="h-4 w-4 text-red-400" />
                <span className="hidden sm:inline">{row.traditional}</span>
              </span>
              <span className="flex items-center justify-center gap-2 text-neutral-300">
                <Check className="h-4 w-4 text-green-400" />
                <span className="hidden sm:inline">{row.guard}</span>
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
