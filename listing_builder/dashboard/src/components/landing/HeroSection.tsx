// src/components/landing/HeroSection.tsx
// Purpose: Hero with badge, headline, CTAs, and Compliance Radar widget
// NOT for: Other landing sections

'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Shield, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { fadeInUp, scaleIn } from '@/lib/animations';
import { radarItems } from '@/lib/landing-data';

const statusConfig = {
  green: { icon: CheckCircle, bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
  yellow: { icon: AlertTriangle, bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' },
  red: { icon: XCircle, bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' },
};

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-[#121212] px-4 pt-32 pb-20 sm:px-6 lg:px-8">
      {/* Subtle radial gradient behind hero */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(34,197,94,0.08)_0%,transparent_60%)]" />

      <div className="relative mx-auto max-w-7xl text-center">
        {/* Badge */}
        <motion.div variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-[#1A1A1A] px-4 py-1.5 text-sm text-neutral-400">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Multi-Marketplace EPR &amp; Product Compliance
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mx-auto mt-8 max-w-4xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl"
        >
          Stop Marketplace{' '}
          <span className="text-green-500">Blocking</span>
          <br />
          Before It Starts
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mx-auto mt-6 max-w-2xl text-lg text-neutral-400"
        >
          AI-powered early warning system for EPR, WEEE &amp; Packaging compliance
          across Amazon, eBay, and Kaufland. Know your risk before the marketplace acts.
        </motion.p>

        {/* CTAs */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <a
            href="#pricing"
            className="inline-flex items-center gap-2 rounded-lg bg-green-500 px-6 py-3 text-sm font-medium text-black transition-colors hover:bg-green-400"
          >
            Start Free Analysis <ArrowRight className="h-4 w-4" />
          </a>
          <a
            href="#how-it-works"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-[#1A1A1A] px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-[#222]"
          >
            See How It Works
          </a>
        </motion.div>

        {/* Compliance Radar widget */}
        <motion.div
          variants={scaleIn}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mx-auto mt-16 max-w-2xl rounded-xl border border-border bg-[#1A1A1A] p-6"
        >
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
              <Shield className="h-5 w-5 text-green-500" />
            </div>
            <div className="text-left">
              <p className="font-semibold text-white">Compliance Radar</p>
              <p className="text-sm text-neutral-500">Real-time risk monitoring</p>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            {radarItems.map((item) => {
              const cfg = statusConfig[item.status];
              const Icon = cfg.icon;
              return (
                <div
                  key={item.label}
                  className={`flex items-center gap-3 rounded-lg border ${cfg.border} ${cfg.bg} px-4 py-3`}
                >
                  <Icon className={`h-5 w-5 shrink-0 ${cfg.text}`} />
                  <span className="text-sm text-neutral-300">{item.label}</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
