// frontend/src/components/ui/__tests__/FlowIndicator.test.tsx
// Purpose: Verify 3-step flow stepper after Mateusz meeting (04.03.2026)
// NOT for: Styling or animation tests

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FlowIndicator } from '../FlowIndicator'

describe('FlowIndicator — meeting Mateusza 04.03.2026', () => {
  it('13. krok 3 ma label "Konwersja" (nie "Eksport")', () => {
    render(<FlowIndicator stats={null} />)
    expect(screen.getByText('Konwersja')).toBeInTheDocument()
    expect(screen.queryByText('Eksport')).not.toBeInTheDocument()
  })

  it('14. krok 3 linkuje do /converter (nie /publish)', () => {
    render(<FlowIndicator stats={null} />)
    const links = screen.getAllByRole('link')
    const lastLink = links[links.length - 1]
    expect(lastLink).toHaveAttribute('href', '/converter')
  })

  it('15. sublabel kroku 3 mówi "do konwersji" gdy są zoptymalizowane produkty', () => {
    render(<FlowIndicator stats={{ total_products: 10, pending_optimization: 0, optimized_products: 5 }} />)
    expect(screen.getByText('5 do konwersji')).toBeInTheDocument()
  })

  it('16. sublabel kroku 3 mówi "Brak gotowych" gdy nie ma zoptymalizowanych', () => {
    render(<FlowIndicator stats={{ total_products: 0, pending_optimization: 0, optimized_products: 0 }} />)
    expect(screen.getByText('Brak gotowych')).toBeInTheDocument()
  })

  it('17. flow ma 3 kroki: Import → Optymalizacja → Konwersja', () => {
    render(<FlowIndicator stats={null} />)
    expect(screen.getByText('Import')).toBeInTheDocument()
    expect(screen.getByText('Optymalizacja')).toBeInTheDocument()
    expect(screen.getByText('Konwersja')).toBeInTheDocument()
  })
})
