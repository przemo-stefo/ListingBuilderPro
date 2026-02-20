// frontend/src/components/landing/FooterSection.tsx
// Purpose: Landing page footer — 5-column layout matching reference design
// NOT for: App footer or navigation

import Link from 'next/link'
import { Sparkles } from 'lucide-react'

export function FooterSection() {
  return (
    <footer className="border-t border-gray-800/50 py-16 px-6">
      <div className="mx-auto max-w-5xl grid grid-cols-2 md:grid-cols-5 gap-8">
        {/* Brand — full width on mobile */}
        <div className="col-span-2 md:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
            </div>
            <span className="text-sm font-semibold text-white">OctoHelper</span>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">
            AI-powered marketplace assistant dla sprzedawców online.
          </p>
        </div>

        {/* Product */}
        <div>
          <h4 className="text-xs font-semibold text-white mb-3">Produkt</h4>
          <ul className="space-y-2">
            <li><a href="#features" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Funkcje</a></li>
            <li><a href="#pricing" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Cennik</a></li>
            <li><a href="#how-it-works" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Jak to działa</a></li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h4 className="text-xs font-semibold text-white mb-3">Firma</h4>
          <ul className="space-y-2">
            <li><a href="#faq" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">FAQ</a></li>
            <li><Link href="/login" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Kontakt</Link></li>
          </ul>
        </div>

        {/* Legal */}
        <div>
          <h4 className="text-xs font-semibold text-white mb-3">Prawne</h4>
          <ul className="space-y-2">
            <li><Link href="/privacy" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Polityka prywatności</Link></li>
            <li><Link href="/terms" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Regulamin</Link></li>
          </ul>
        </div>

        {/* Support */}
        <div>
          <h4 className="text-xs font-semibold text-white mb-3">Wsparcie</h4>
          <ul className="space-y-2">
            <li><Link href="/login" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Panel klienta</Link></li>
          </ul>
        </div>
      </div>

      <div className="mx-auto max-w-5xl mt-12 pt-8 border-t border-gray-800/50 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-xs text-gray-600">
          &copy; {new Date().getFullYear()} PYROX AI, LLC. Wszelkie prawa zastrzeżone.
        </p>
        <p className="text-xs text-gray-600">
          Stworzone dla sprzedawców marketplace
        </p>
      </div>
    </footer>
  )
}
