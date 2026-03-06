// frontend/src/components/ui/__tests__/OnboardingChecklist.test.tsx
// Purpose: Verify onboarding checklist after Mateusz meeting (04.03.2026)
// NOT for: Full onboarding flow or localStorage logic

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OnboardingChecklist } from '../OnboardingChecklist'

// WHY: useLocalStorage reads localStorage — clear before each test
beforeEach(() => {
  localStorage.clear()
})

const defaultProps = {
  totalProducts: 0,
  optimizedCount: 0,
  publishedCount: 0,
  hasOAuth: false,
}

describe('OnboardingChecklist — meeting Mateusza 04.03.2026', () => {
  it('18. krok 4 ma label "Konwertuj listing" (nie "Eksportuj na marketplace")', () => {
    render(<OnboardingChecklist {...defaultProps} />)
    expect(screen.getByText('Konwertuj listing')).toBeInTheDocument()
    expect(screen.queryByText('Eksportuj na marketplace')).not.toBeInTheDocument()
  })

  it('19. krok 4 linkuje do /converter (nie /publish)', () => {
    render(<OnboardingChecklist {...defaultProps} />)
    const links = screen.getAllByRole('link')
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/converter')
    expect(hrefs).not.toContain('/publish')
  })

  it('20. checklist nadal ma 4 kroki w poprawnej kolejności', () => {
    render(<OnboardingChecklist {...defaultProps} />)
    const labels = screen.getAllByRole('link').map(l => l.textContent?.trim())
    expect(labels).toEqual([
      'Połącz Allegro',
      'Importuj produkt',
      'Zoptymalizuj listing',
      'Konwertuj listing',
    ])
  })
})
