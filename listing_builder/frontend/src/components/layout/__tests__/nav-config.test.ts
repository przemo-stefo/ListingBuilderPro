// frontend/src/components/layout/__tests__/nav-config.test.ts
// Purpose: Verify navigation structure after Mateusz changes (25.03.2026)
// NOT for: Sidebar rendering or visual tests

import { describe, it, expect } from 'vitest'
import { navSections } from '../nav-config'

// WHY: Helper to find a section by label
const findSection = (label: string) => navSections.find(s => s.label === label)
const findItem = (sectionLabel: string, title: string) =>
  findSection(sectionLabel)?.items.find(i => i.title === title)

describe('nav-config — Mateusz 25.03.2026', () => {
  // --- Sekcja "Główne" ---

  it('1. sekcja "Główne" istnieje', () => {
    expect(findSection('Główne')).toBeDefined()
  })

  it('2. sekcja "Główne" ma 10 pozycji', () => {
    expect(findSection('Główne')!.items).toHaveLength(10)
  })

  it('3. kolejność pierwszych 6 w "Główne"', () => {
    const titles = findSection('Główne')!.items.map(i => i.title)
    expect(titles.slice(0, 6)).toEqual([
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

  it('7. Optymalizator nie ma premiumOnly', () => {
    expect(findItem('Główne', 'Optymalizator')).not.toHaveProperty('premiumOnly')
  })

  // --- Usunięte elementy ---

  it('8. "Eksport do pliku" NIE istnieje w żadnej sekcji', () => {
    const allItems = navSections.flatMap(s => s.items)
    expect(allItems.find(i => i.title === 'Eksport do pliku')).toBeUndefined()
  })

  it('9. żaden link nie prowadzi do /publish', () => {
    const allHrefs = navSections.flatMap(s => s.items.map(i => i.href))
    expect(allHrefs).not.toContain('/publish')
  })

  it('10. sekcja "Demo" z Amazon Pro NIE istnieje', () => {
    expect(findSection('Demo')).toBeUndefined()
  })

  it('11. sekcja "Optymalizacja AI" NIE istnieje', () => {
    expect(findSection('Optymalizacja AI')).toBeUndefined()
  })

  it('12. Optymalizator pojawia się TYLKO RAZ w całej nawigacji', () => {
    const allItems = navSections.flatMap(s => s.items)
    const count = allItems.filter(i => i.title === 'Optymalizator').length
    expect(count).toBe(1)
  })

  it('13. żaden item nie ma premiumOnly', () => {
    const allItems = navSections.flatMap(s => s.items)
    const premium = allItems.filter(i => 'premiumOnly' in i)
    expect(premium).toHaveLength(0)
  })
})
