// frontend/src/components/layout/nav-config.ts
// Purpose: Sidebar navigation structure — sections, items, icons, descriptions
// NOT for: Rendering logic (that's Sidebar.tsx)

import {
  LayoutDashboard,
  Upload,
  ArrowRightLeft,
  Sparkles,
  Brain,
  Users,
  BarChart3,
  Search,
  Bell,
  AlertTriangle,
  Link2,
  FileBarChart,
  FileDown,
  Database,
  DollarSign,
} from 'lucide-react'

export interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  premiumOnly?: boolean
  desc?: string
  // WHY: Expert AI gets green accent to stand out as key feature
  highlight?: boolean
}

export interface NavSection {
  label: string
  items: NavItem[]
}

// WHY: Sidebar order: Pulpit→Import→Baza Produktów→Integracje→Konwerter | Optymalizator→Eksport→Ekspert AI→Badanie rynku
export const navSections: NavSection[] = [
  {
    label: 'Główne',
    items: [
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard, desc: 'Przegląd statystyk i szybkie akcje' },
      { title: 'Import', href: '/products/import', icon: Upload, desc: 'Importuj produkty z CSV lub Allegro' },
      { title: 'Baza Produktów', href: '/products', icon: Database, desc: 'Przeglądaj, filtruj i zarządzaj zaimportowanymi produktami' },
      { title: 'Integracje', href: '/integrations', icon: Link2, desc: 'Połączenia OAuth z marketplace (Amazon, Allegro, eBay...)' },
      { title: 'Konwerter', href: '/converter', icon: ArrowRightLeft, desc: 'Konwertuj oferty Allegro na Amazon/eBay/Kaufland' },
    ],
  },
  {
    label: 'Optymalizacja AI',
    items: [
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles, desc: 'AI generuje tytuł, bullety, opis i słowa kluczowe backend' },
      { title: 'Eksport do pliku', href: '/publish', icon: FileDown, desc: 'Pobierz zoptymalizowane listingi jako plik CSV/TSV do uploadu na marketplace' },
      { title: 'Ekspert AI', href: '/expert-qa', icon: Brain, desc: 'Zadaj pytanie ekspertowi AI o sprzedaży na marketplace', highlight: true },
      { title: 'Badanie rynku', href: '/research', icon: Users, desc: '10 skilli AI: badanie klienta, ICP, brief, reklamy Facebook/Google, skrypty wideo' },
    ],
  },
  {
    label: 'Admin',
    items: [
      { title: 'Koszty API', href: '/admin', icon: DollarSign, desc: 'Zużycie tokenów, koszty per provider, trend dzienny' },
    ],
  },
]

// WHY: Compliance sub-tabs defined here so sidebar shows them as expandable menu
export const complianceSubItems = [
  { key: 'dashboard', label: 'Panel Główny', icon: BarChart3, desc: 'Przegląd zgodności i statusu regulacji' },
  { key: 'audit', label: 'Audyt', icon: Search, desc: 'Sprawdź zgodność produktów z regulacjami' },
  { key: 'settings', label: 'Aktywacja Alertów', icon: Bell, desc: 'Włącz/wyłącz powiadomienia o zmianach regulacji' },
  { key: 'alerts', label: 'Alerty', icon: AlertTriangle, desc: 'Lista alertów i zmian regulacji' },
  { key: 'integrations', label: 'Integracje', icon: Link2, desc: 'Połączenia z marketplace i serwisami zewnętrznymi' },
  { key: 'upload', label: 'Upload', icon: Upload, desc: 'Wgraj dokumenty zgodności i certyfikaty' },
  { key: 'epr', label: 'Raporty EPR', icon: FileBarChart, desc: 'Raporty EPR wymagane przez regulacje UE' },
]
