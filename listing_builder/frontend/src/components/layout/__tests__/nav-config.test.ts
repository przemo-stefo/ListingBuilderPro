// frontend/src/components/layout/__tests__/nav-config.test.ts
// Purpose: Verify navigation structure after Mateusz meeting (04.03.2026)
// NOT for: Sidebar rendering or visual tests

import { describe, it, expect } from 'vitest'
import { navSections } from '../nav-config'

// WHY: Helper to find a section by label
const findSection = (label: string) => navSections.find(s => s.label === label)
const findItem = (sectionLabel: string, title: string) =>
  findSection(sectionLabel)?.items.find(i => i.title === title)

describe('nav-config — meeting Mateusza 04.03.2026', () => {
  // --- Sekcja "Główne": kolejność Import → Baza → Optymalizator → Konwerter ---

  it('1. sekcja "Główne" istnieje', () => {
    expect(findSection('Główne')).toBeDefined()
  })

  it('2. sekcja "Główne" ma 6 pozycji', () => {
    expect(findSection('Główne')!.items).toHaveLength(6)
  })

  it('3. kolejność w "Główne": Pulpit → Import → Baza → Optymalizator → Konwerter → Listing Score', () => {
    const titles = findSection('Główne')!.items.map(i => i.title)
    expect(titles).toEqual([
      'Pulpit',
      'Import',
      'Baza Produktów',
      'Optymalizator',
      'Konwerter',
      'Listing Score',
    ])
  })

  it('4. Optymalizator jest po Bazie Produktów', () => {
    const items = findSection('Główne')!.items
    const bazaIdx = items.findIndex(i => i.title === 'Baza Produktów')
    const optIdx = items.findIndex(i => i.title === 'Optymalizator')
    expect(optIdx).toBe(bazaIdx + 1)
  })

  it('5. Optymalizator jest przed Konwerterem', () => {
    const items = findSection('Główne')!.items
    const optIdx = items.findIndex(i => i.title === 'Optymalizator')
    const convIdx = items.findIndex(i => i.title === 'Konwerter')
    expect(optIdx).toBe(convIdx - 1)
  })

  it('6. Optymalizator w "Główne" ma href /optimize', () => {
    expect(findItem('Główne', 'Optymalizator')!.href).toBe('/optimize')
  })

  it('7. Optymalizator w "Główne" jest premiumOnly', () => {
    expect(findItem('Główne', 'Optymalizator')!.premiumOnly).toBe(true)
  })

  // --- Usunięcie "Eksport do pliku" ---

  it('8. "Eksport do pliku" NIE istnieje w żadnej sekcji', () => {
    const allItems = navSections.flatMap(s => s.items)
    const eksport = allItems.find(i => i.title === 'Eksport do pliku')
    expect(eksport).toBeUndefined()
  })

  it('9. żaden link nie prowadzi do /publish', () => {
    const allHrefs = navSections.flatMap(s => s.items.map(i => i.href))
    expect(allHrefs).not.toContain('/publish')
  })

  // --- Optymalizator usunięty z "Optymalizacja AI" ---

  it('10. sekcja "Optymalizacja AI" NIE zawiera Optymalizatora', () => {
    expect(findItem('Optymalizacja AI', 'Optymalizator')).toBeUndefined()
  })

  it('11. sekcja "Optymalizacja AI" zaczyna się od Ekspert Amazon', () => {
    const first = findSection('Optymalizacja AI')!.items[0]
    expect(first.title).toBe('Ekspert Amazon')
  })

  it('12. Optymalizator pojawia się TYLKO RAZ w całej nawigacji', () => {
    const allItems = navSections.flatMap(s => s.items)
    const count = allItems.filter(i => i.title === 'Optymalizator').length
    expect(count).toBe(1)
  })
})
