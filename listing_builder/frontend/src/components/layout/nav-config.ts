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
  Bell,
  AlertTriangle,
  FileBarChart,
  Database,
  DollarSign,
  Rocket,
  Tags,
  Sparkles,
} from 'lucide-react'

export interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  premiumOnly?: boolean
  desc?: string
  // WHY: Expert AI gets green accent to stand out as key feature
  highlight?: boolean
  // WHY: Beta features get amber badge in sidebar
  beta?: boolean
}

export interface NavSection {
  label: string
  items: NavItem[]
}

// WHY: Mateusz (18.03) — 3 moduły w subskrypcji: Listing Score, Walidator, Ekspert Kaufland. Bez premium gate.
export const navSections: NavSection[] = [
  {
    label: 'Główne',
    items: [
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard, desc: 'Przegląd statystyk i szybkie akcje' },
      { title: 'Import', href: '/products/import', icon: Upload, desc: 'Importuj produkty z CSV lub Allegro' },
      { title: 'Baza Produktów', href: '/products', icon: Database, desc: 'Przeglądaj, filtruj i zarządzaj zaimportowanymi produktami' },
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles, premiumOnly: true, desc: 'Optymalizuj tytuły i opisy pod SEO marketplace' },
      { title: 'Konwerter', href: '/converter', icon: ArrowRightLeft, desc: 'Konwertuj oferty Allegro na Amazon/eBay/Kaufland' },
      { title: 'Listing Score', href: '/listing-score', icon: BarChart3, desc: 'Oceń listing 1-10 w 5 wymiarach copywriterskich' },
      { title: 'Walidator', href: '/validator', icon: Search, desc: 'Sprawdź potencjał produktu' },
      { title: 'Ekspert Kaufland', href: '/expert-qa?mode=kaufland', icon: Store, desc: 'Pytania o Kaufland — listingi, SEO, kategorie, EAN, wysyłka, GPSR' },
      { title: 'Auto-Atrybuty', href: '/attributes', icon: Tags, desc: 'Wygeneruj atrybuty produktowe', beta: true },
    ],
  },
  {
    label: 'Demo',
    items: [
      { title: 'Amazon Pro', href: '/demo/amazon-pro', icon: Rocket, premiumOnly: true, desc: 'Pełny pipeline: ASIN → AI → Compliance → Publish → Coupon', highlight: true },
    ],
  },
  {
    label: 'Admin',
    items: [
      { title: 'Panel Admin', href: '/admin', icon: DollarSign, desc: 'Przegląd systemu, licencje, koszty API' },
    ],
  },
]

// WHY: Compliance sub-tabs defined here so sidebar shows them as expandable menu
export const complianceSubItems = [
  { key: 'dashboard', label: 'Panel Główny', icon: BarChart3, desc: 'Przegląd zgodności i statusu regulacji' },
  { key: 'audit', label: 'Audyt', icon: Search, desc: 'Sprawdź zgodność produktów z regulacjami' },
  { key: 'settings', label: 'Aktywacja Alertów', icon: Bell, desc: 'Włącz/wyłącz powiadomienia o zmianach regulacji' },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle, desc: 'Lista alertów i zmian regulacji' },
  { key: 'upload', label: 'Upload', icon: Upload, desc: 'Wgraj dokumenty zgodności i certyfikaty' },
  { key: 'epr', label: 'Raporty EPR', icon: FileBarChart, desc: 'Raporty EPR wymagane przez regulacje UE' },
]
