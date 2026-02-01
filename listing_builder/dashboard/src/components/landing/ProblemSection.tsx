// src/components/landing/ProblemSection.tsx
// Purpose: Pain points grid showing why compliance matters
// NOT for: Solutions or feature descriptions

'use client';

import { motion } from 'framer-motion';
import { Eye, ShoppingCart, Ban, CreditCard } from 'lucide-react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { painPoints } from '@/lib/landing-data';

const iconMap: Record<string, React.ElementType> = {
  Eye, ShoppingCart, Ban, CreditCard,
};

export function ProblemSection() {
  return (
    <section className="bg-[#1A1A1A] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl items-start gap-16 lg:grid-cols-2">
        {/* Left: illustration placeholder */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="flex aspect-[4/3] items-center justify-center rounded-xl border border-border bg-[#121212]"
        >
          <div className="text-center text-neutral-600">
            <p className="text-6xl">&#128683;</p>
            <p className="mt-2 text-sm">Marketplace Enforcement</p>
          </div>
        </motion.div>

        {/* Right: content */}
        <div>
          <motion.h2
            variants={fadeInUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="text-3xl font-bold text-white sm:text-4xl"
          >
            Marketplaces Block First,
            <br />
            <span className="text-neutral-500">Ask Questions Later</span>
          </motion.h2>

          <motion.p
            variants={fadeInUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mt-4 text-neutral-400"
          >
            EU compliance requirements are complex and constantly changing.
            Amazon, eBay, and Kaufland enforce aggressively – often without prior notice.
          </motion.p>

          {/* Pain point cards */}
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2"
          >
            {painPoints.map((point) => {
              const Icon = iconMap[point.icon];
              return (
                <motion.div
                  key={point.title}
                  variants={staggerItem}
                  className="rounded-lg border border-border bg-[#121212] p-5"
                >
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
                    <Icon className="h-5 w-5 text-red-400" />
                  </div>
                  <h3 className="font-semibold text-white">{point.title}</h3>
                  <p className="mt-1 text-sm text-neutral-400">{point.description}</p>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Blockquote */}
          <motion.blockquote
            variants={fadeInUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="mt-6 rounded-lg border-l-2 border-neutral-600 bg-[#121212] px-5 py-4 text-sm text-neutral-400"
          >
            Today&apos;s compliance is <span className="font-semibold text-red-400">reactive</span>.
            You find out when it&apos;s too late.
          </motion.blockquote>
        </div>
      </div>
    </section>
  );
}
