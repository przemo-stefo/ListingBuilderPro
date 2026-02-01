// src/components/landing/Navbar.tsx
// Purpose: Fixed top navigation with mobile hamburger menu
// NOT for: Dashboard sidebar navigation

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Menu, X } from 'lucide-react';
import { navLinks } from '@/lib/landing-data';

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/20">
            <Shield className="h-5 w-5 text-green-500" />
          </div>
          <span className="text-lg font-semibold text-white">AI Compliance Guard</span>
        </a>

        {/* Desktop links */}
        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-neutral-400 transition-colors hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Desktop CTAs */}
        <div className="hidden items-center gap-3 md:flex">
          <a href="/dashboard" className="text-sm text-neutral-400 hover:text-white">
            Sign In
          </a>
          <a
            href="#pricing"
            className="rounded-lg bg-green-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-green-400"
          >
            Start Free Trial
          </a>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="text-neutral-400 md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t border-border bg-background px-4 py-4 md:hidden"
        >
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="text-sm text-neutral-400 hover:text-white"
              >
                {link.label}
              </a>
            ))}
            <a href="/dashboard" className="text-sm text-neutral-400 hover:text-white">
              Sign In
            </a>
            <a
              href="#pricing"
              className="rounded-lg bg-green-500 px-4 py-2 text-center text-sm font-medium text-black"
            >
              Start Free Trial
            </a>
          </div>
        </motion.div>
      )}
    </nav>
  );
}
