// src/components/landing/Footer.tsx
// Purpose: Footer with logo, link columns, and copyright
// NOT for: Navigation bar or CTA sections

import { Shield } from 'lucide-react';
import { footerLinks } from '@/lib/landing-data';

export function Footer() {
  return (
    <footer className="border-t border-border bg-[#121212] px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-5">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/20">
                <Shield className="h-5 w-5 text-green-500" />
              </div>
              <span className="font-semibold text-white">Guard</span>
            </div>
            <p className="mt-3 text-sm text-neutral-500">
              AI-powered compliance monitoring for EU marketplace sellers.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-sm font-semibold text-white">{category}</h4>
              <ul className="mt-3 space-y-2">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-neutral-500 transition-colors hover:text-neutral-300"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-sm text-neutral-600">
            &copy; {new Date().getFullYear()} AI Compliance Guard. All rights reserved.
          </p>
          <p className="flex items-center gap-1 text-sm text-neutral-600">
            <span className="inline-block h-3 w-4 rounded-sm bg-blue-800" />
            Made for EU Sellers
          </p>
        </div>
      </div>
    </footer>
  );
}
