// frontend/src/__tests__/integration/mateusz-flow-040326.test.tsx
// Purpose: 2 full integration tests verifying Mateusz meeting changes (04.03.2026)
// NOT for: Unit tests of individual components (see __tests__/ in each component dir)

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { navSections } from '@/components/layout/nav-config'
import { FlowIndicator } from '@/components/ui/FlowIndicator'
import { OnboardingChecklist } from '@/components/ui/OnboardingChecklist'

// WHY: ImportPage uses useRouter — mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
}))

beforeEach(() => {
  localStorage.clear()
})

describe('Meeting Mateusza 04.03.2026 — pełny test flow', () => {
  // ============================================================
  // TEST 1: Cała nawigacja i dashboard widoczne dla Mateusza
  // Import → Optymalizacja → Konwersja (bez Eksportu)
  // ============================================================
  it('FULL TEST 1: nawigacja + stepper + checklist — nowy flow bez Eksportu', () => {
    // --- NAV-CONFIG: struktura sidebaru ---
    const glowne = navSections.find(s => s.label === 'Główne')!
    const aiSection = navSections.find(s => s.label === 'Optymalizacja AI')!
    const allItems = navSections.flatMap(s => s.items)

    // Sekcja "Główne" ma poprawną kolejność
    const glowneTitles = glowne.items.map(i => i.title)
    expect(glowneTitles).toEqual([
      'Pulpit', 'Import', 'Baza Produktów', 'Optymalizator', 'Konwerter', 'Listing Score',
    ])

    // Optymalizator JEST w Główne, NIE MA w Optymalizacja AI
    expect(glowne.items.some(i => i.title === 'Optymalizator')).toBe(true)
    expect(aiSection.items.some(i => i.title === 'Optymalizator')).toBe(false)

    // "Eksport do pliku" nie istnieje nigdzie
    expect(allItems.find(i => i.title === 'Eksport do pliku')).toBeUndefined()

    // Żaden link nie prowadzi do /publish
    expect(allItems.map(i => i.href)).not.toContain('/publish')

    // Optymalizator jest premium
    const opt = glowne.items.find(i => i.title === 'Optymalizator')!
    expect(opt.premiumOnly).toBe(true)
    expect(opt.href).toBe('/optimize')

    // --- FLOW INDICATOR: stepper na dashboardzie ---
    const { unmount } = render(
      <FlowIndicator stats={{ total_products: 15, pending_optimization: 3, optimized_products: 8 }} />
    )

    // 3 kroki widoczne
    expect(screen.getByText('Import')).toBeInTheDocument()
    expect(screen.getByText('Optymalizacja')).toBeInTheDocument()
    expect(screen.getByText('Konwersja')).toBeInTheDocument()

    // Brak "Eksport"
    expect(screen.queryByText('Eksport')).not.toBeInTheDocument()

    // Krok 3 linkuje do /converter
    const links = screen.getAllByRole('link')
    expect(links[2]).toHaveAttribute('href', '/converter')

    // Sublabel pokazuje "do konwersji"
    expect(screen.getByText('8 do konwersji')).toBeInTheDocument()

    unmount()

    // --- ONBOARDING CHECKLIST ---
    render(
      <OnboardingChecklist totalProducts={0} optimizedCount={0} publishedCount={0} hasOAuth={false} />
    )

    // Krok 4 = "Konwertuj listing", nie "Eksportuj"
    expect(screen.getByText('Konwertuj listing')).toBeInTheDocument()
    expect(screen.queryByText('Eksportuj na marketplace')).not.toBeInTheDocument()

    // Krok 4 linkuje do /converter
    const checklistLinks = screen.getAllByRole('link')
    const checklistHrefs = checklistLinks.map(l => l.getAttribute('href'))
    expect(checklistHrefs).toContain('/converter')
    expect(checklistHrefs).not.toContain('/publish')

    // Poprawna kolejność kroków
    const labels = checklistLinks.map(l => l.textContent?.trim())
    expect(labels).toEqual([
      'Połącz Allegro', 'Importuj produkt', 'Zoptymalizuj listing', 'Konwertuj listing',
    ])
  })

  // ============================================================
  // TEST 2: Różne stany danych — Mateusz widzi poprawne sublabels
  // ============================================================
  it('FULL TEST 2: sublabels i stany — nowy użytkownik, w trakcie, po optymalizacji', () => {
    // --- Stan A: Nowy użytkownik (0 produktów) ---
    const { unmount: unmountA } = render(<FlowIndicator stats={null} />)

    expect(screen.getByText('Zacznij tutaj')).toBeInTheDocument()
    expect(screen.getByText('Brak produktów')).toBeInTheDocument()
    expect(screen.getByText('Brak gotowych')).toBeInTheDocument()
    expect(screen.getByText('Konwersja')).toBeInTheDocument()
    unmountA()

    // --- Stan B: Produkty zaimportowane, nic nie zoptymalizowane ---
    const { unmount: unmountB } = render(
      <FlowIndicator stats={{ total_products: 20, pending_optimization: 20, optimized_products: 0 }} />
    )

    expect(screen.getByText('20 czeka')).toBeInTheDocument()
    expect(screen.getByText('Brak gotowych')).toBeInTheDocument() // krok Konwersja
    unmountB()

    // --- Stan C: Część zoptymalizowana — gotowa do konwersji ---
    const { unmount: unmountC } = render(
      <FlowIndicator stats={{ total_products: 50, pending_optimization: 10, optimized_products: 40 }} />
    )

    expect(screen.getByText('10 czeka')).toBeInTheDocument()
    expect(screen.getByText('40 do konwersji')).toBeInTheDocument()
    unmountC()

    // --- Stan D: Wszystko zoptymalizowane ---
    const { unmount: unmountD } = render(
      <FlowIndicator stats={{ total_products: 30, pending_optimization: 0, optimized_products: 30 }} />
    )

    expect(screen.getByText('30 gotowych')).toBeInTheDocument()
    expect(screen.getByText('30 do konwersji')).toBeInTheDocument()
    unmountD()

    // --- OnboardingChecklist: częściowo ukończony ---
    render(
      <OnboardingChecklist totalProducts={5} optimizedCount={2} publishedCount={0} hasOAuth={true} />
    )

    // 2 z 4 kroków ukończone (Połącz Allegro + Importuj + Zoptymalizuj)
    expect(screen.getByText('3/4 kroków ukończonych')).toBeInTheDocument()

    // Krok "Konwertuj listing" nadal do zrobienia (publishedCount=0)
    expect(screen.getByText('Konwertuj listing')).toBeInTheDocument()
  })

  // ============================================================
  // TEST 3: Strona Import — brak taba "Pojedynczy"
  // ============================================================
  it('FULL TEST 3: Import page — tylko 2 taby (Import zbiorczy, Z konta Allegro), brak Pojedynczy', async () => {
    const ImportPage = (await import('@/app/products/import/page')).default
    render(<ImportPage />)

    // 2 taby widoczne
    expect(screen.getByText('Import zbiorczy')).toBeInTheDocument()
    expect(screen.getByText('Z konta Allegro')).toBeInTheDocument()

    // Tab "Pojedynczy" NIE istnieje
    expect(screen.queryByText('Pojedynczy')).not.toBeInTheDocument()

    // Opis strony zaktualizowany
    expect(screen.getByText(/Dodaj produkty z CSV lub konta Allegro/)).toBeInTheDocument()

    // Domyślnie aktywny "Import zbiorczy"
    const batchButton = screen.getByText('Import zbiorczy').closest('button')
    expect(batchButton?.className).toContain('bg-white/10')
  })
})
