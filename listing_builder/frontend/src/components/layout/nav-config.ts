// frontend/src/components/layout/nav-config.ts
// Purpose: Sidebar navigation structure — sections, items, icons, descriptions
// NOT for: Rendering logic (that's Sidebar.tsx)

import {
  LayoutDashboard,
  Upload,
  ArrowRightLeft,
  Sparkles,
  Brain,
  ShoppingCart,
  Store,
  Users,
  BarChart3,
  Search,
  Bell,
  AlertTriangle,
  FileBarChart,
  FileDown,
  Database,
  DollarSign,
  Megaphone,
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

// WHY: Free tier = Import, Baza Produktów, Konwerter, Listing Score. Premium = rest.
export const navSections: NavSection[] = [
  {
    label: 'Główne',
    items: [
      { title: 'Pulpit', href: '/dashboard', icon: LayoutDashboard, desc: 'Przegląd statystyk i szybkie akcje' },
      { title: 'Import', href: '/products/import', icon: Upload, desc: 'Importuj produkty z CSV lub Allegro' },
      { title: 'Baza Produktów', href: '/products', icon: Database, desc: 'Przeglądaj, filtruj i zarządzaj zaimportowanymi produktami' },
      { title: 'Konwerter', href: '/converter', icon: ArrowRightLeft, desc: 'Konwertuj oferty Allegro na Amazon/eBay/Kaufland' },
      // WHY: Mateusz (spotkanie 24.02) — Listing Score tuż pod konwersją
      { title: 'Listing Score', href: '/listing-score', icon: BarChart3, desc: 'Oceń listing 1-10 w 5 wymiarach copywriterskich' },
    ],
  },
  {
    label: 'Optymalizacja AI',
    items: [
      { title: 'Optymalizator', href: '/optimize', icon: Sparkles, desc: 'AI generuje tytuł, bullety, opis i słowa kluczowe backend', premiumOnly: true },
      { title: 'Eksport do pliku', href: '/publish', icon: FileDown, desc: 'Pobierz zoptymalizowane listingi jako plik CSV/TSV do uploadu na marketplace', premiumOnly: true },
      { title: 'Ekspert Amazon', href: '/expert-qa?mode=strict', icon: ShoppingCart, desc: 'Pytania o Amazon — odpowiedzi tylko z bazy wiedzy kursów', premiumOnly: true },
      { title: 'Ekspert Kaufland', href: '/expert-qa?mode=kaufland', icon: Store, desc: 'Pytania o Kaufland — listingi, SEO, kategorie, EAN, wysyłka', premiumOnly: true },
      { title: 'Reklamy AI', href: '/ad-copy', icon: Megaphone, desc: '3 warianty reklam (hook, story, benefit) z wiedzy ekspertów', premiumOnly: true, beta: true },
      { title: 'Badanie rynku', href: '/research', icon: Users, desc: '10 skilli AI: badanie klienta, ICP, brief, reklamy Facebook/Google, skrypty wideo', premiumOnly: true, beta: true },
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
