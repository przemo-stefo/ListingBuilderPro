// src/components/landing/FeaturesSection.tsx
// Purpose: 6 feature cards with category badges
// NOT for: Alerts or pricing content

'use client';

import { motion } from 'framer-motion';
import { Radar, TrendingUp, FileText, Timer, Globe, BarChart3 } from 'lucide-react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { features } from '@/lib/landing-data';

const iconMap: Record<string, React.ElementType> = {
  Radar, TrendingUp, FileText, Timer, Globe, BarChart3,
};

export function FeaturesSection() {
  return (
    <section id="features" className="bg-[#1A1A1A] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="text-center"
        >
          <span className="text-sm font-medium tracking-wider text-green-500">FEATURES</span>
          <h2 className="mt-3 text-3xl font-bold text-white sm:text-4xl">
            Everything You Need for{' '}
            <span className="text-green-500">Compliance Peace of Mind</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-neutral-400">
            Built for cross-border sellers managing complex EPR obligations across multiple marketplaces.
          </p>
        </motion.div>

        {/* Feature cards - 3 cols */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
        >
          {features.map((feature) => {
            const Icon = iconMap[feature.icon];
            return (
              <motion.div
                key={feature.title}
                variants={staggerItem}
                className="rounded-xl border border-border bg-[#121212] p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10">
                    <Icon className="h-6 w-6 text-green-500" />
                  </div>
                  <span className="rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400">
                    {feature.badge}
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{feature.title}</h3>
                <p className="mt-2 text-sm text-neutral-400">{feature.description}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
