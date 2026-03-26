// frontend/src/components/layout/nav-config.ts
// Purpose: Sidebar navigation structure — sections, items, icons, descriptions
// NOT for: Rendering logic (that's Sidebar.tsx)

import {
  LayoutDashboard,
  Upload,
  ArrowRightLeft,
  Store,
  BarChart3,
  Search,
  Database,
  DollarSign,
  Tags,
  Sparkles,
  Stethoscope,
  Megaphone,
} from 'lucide-react'

export interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  desc?: string
  // WHY: Beta features get amber badge in sidebar
  beta?: boolean
  // WHY: betaOnly items are hidden from non-beta-testers entirely
  betaOnly?: boolean
}

export interface NavSection {
  label: string
  items: NavItem[]
}

// WHY: Mateusz (25.03) — no premium gating, no Amazon Pro, no Compliance Guard, no export
export const navSections: NavSection[] = [
  {
    label: 'Główne',
    items: [
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard, desc: 'Przegląd statystyk i szybkie akcje' },
      { title: 'Import', href: '/products/import', icon: Upload, desc: 'Importuj produkty z CSV lub Allegro' },
      { title: 'Baza Produktów', href: '/products', icon: Database, desc: 'Przeglądaj, filtruj i zarządzaj zaimportowanymi produktami' },
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles, desc: 'Optymalizuj tytuły i opisy pod SEO marketplace' },
      { title: 'Konwerter', href: '/converter', icon: ArrowRightLeft, desc: 'Konwertuj oferty Allegro na Amazon/eBay/Kaufland' },
      { title: 'Listing Score', href: '/listing-score', icon: BarChart3, desc: 'Oceń listing 1-10 w 5 wymiarach copywriterskich' },
      { title: 'Walidator', href: '/validator', icon: Search, desc: 'Sprawdź potencjał produktu' },
      { title: 'Ekspert Kaufland', href: '/expert-qa?mode=kaufland', icon: Store, desc: 'Pytania o Kaufland — listingi, SEO, kategorie, EAN, wysyłka, GPSR' },
      { title: 'Auto-Atrybuty', href: '/attributes', icon: Tags, desc: 'Wygeneruj atrybuty produktowe', beta: true },
      { title: 'Catalog Health', href: '/catalog-health', icon: Stethoscope, desc: 'Skanuj katalog Amazon — wykrywaj i naprawiaj problemy', beta: true },
    ],
  },
  {
    label: 'Meta Ads Lab',
    items: [
      { title: 'Meta Ads Studio', href: '/meta-ads', icon: Megaphone, desc: 'Generuj reklamy, nagłówki, hooki video i briefy kreatywne AI', beta: true, betaOnly: true },
    ],
  },
  {
    label: 'Admin',
    items: [
      { title: 'Panel Admin', href: '/admin', icon: DollarSign, desc: 'Przegląd systemu, licencje, koszty API' },
    ],
  },
]
