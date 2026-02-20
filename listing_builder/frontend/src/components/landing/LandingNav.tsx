// frontend/src/components/landing/LandingNav.tsx
// Purpose: Sticky navigation bar for landing page — logo, section links, CTA
// NOT for: App navigation (that's Sidebar)

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Sparkles, Menu, X } from 'lucide-react'

const NAV_LINKS = [
  { label: 'Funkcje', href: '#features' },
  { label: 'Jak to działa', href: '#how-it-works' },
  { label: 'Cennik', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
]

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  // WHY: passive: true — scroll listener must not block main thread
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav aria-label="Nawigacja główna" className={`fixed top-0 left-0 right-0 z-50 transition-all ${
      scrolled ? 'bg-[#0A0A0A]/80 backdrop-blur-xl border-b border-gray-800/50' : 'bg-transparent'
    }`}>
      <div className="mx-auto max-w-6xl flex items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/landing" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="h-4 w-4 text-emerald-400" />
          </div>
          <span className="text-lg font-semibold text-white">OctoHelper</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map(link => (
            <a key={link.href} href={link.href} className="text-sm text-gray-400 hover:text-white transition-colors">
              {link.label}
            </a>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2">
            Zaloguj się
          </Link>
          <Link href="/login" className="text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-400 px-5 py-2.5 rounded-lg transition-colors">
            Wypróbuj za darmo
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <button onClick={() => setMobileOpen(!mobileOpen)} aria-expanded={mobileOpen} aria-label="Menu mobilne"
          className="md:hidden text-gray-400 hover:text-white">
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-[#0A0A0A]/95 backdrop-blur-xl border-t border-gray-800/50 px-6 py-4 space-y-3">
          {NAV_LINKS.map(link => (
            <a key={link.href} href={link.href} onClick={() => setMobileOpen(false)}
              className="block text-sm text-gray-400 hover:text-white transition-colors py-2">
              {link.label}
            </a>
          ))}
          <Link href="/login" onClick={() => setMobileOpen(false)}
            className="block text-center text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-400 px-5 py-2.5 rounded-lg transition-colors mt-3">
            Wypróbuj za darmo
          </Link>
        </div>
      )}
    </nav>
  )
}
