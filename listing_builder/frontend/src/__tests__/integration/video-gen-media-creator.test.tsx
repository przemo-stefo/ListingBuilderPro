// frontend/src/__tests__/integration/video-gen-media-creator.test.tsx
// Purpose: Full user flow tests for Kreator mediow AI — all 10 marketplaces + image mode
// NOT for: Backend API tests or ComfyUI pipeline tests

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// WHY: vi.hoisted() runs before vi.mock() — allows sharing mocks with factories
const { mockToast, mockPost, mockStartGeneration, mockAddJob, mockInvalidateQueries } = vi.hoisted(() => ({
  mockToast: vi.fn(),
  mockPost: vi.fn(),
  mockStartGeneration: vi.fn(),
  mockAddJob: vi.fn(),
  mockInvalidateQueries: vi.fn(),
}))

vi.mock('@/lib/hooks/useTier', () => ({
  useTier: () => ({ isPremium: true, isLoading: false, tier: 'premium' }),
}))

vi.mock('@/lib/hooks/useToast', () => ({
  useToast: () => ({ toast: mockToast }),
}))

vi.mock('@/lib/api/client', () => ({
  apiClient: { post: mockPost },
}))

vi.mock('@/components/tier/PremiumGate', () => ({
  PremiumGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// WHY: Mock MediaGenProvider — provides global context for background generation
vi.mock('@/components/providers/MediaGenProvider', () => ({
  useMediaGen: () => ({ activeJobs: [], addJob: mockAddJob, completedJobIds: [], clearCompleted: vi.fn() }),
}))

// WHY: Mock startGeneration API call — image generation now goes through background API
vi.mock('@/lib/api/mediaGeneration', () => ({
  startGeneration: mockStartGeneration,
}))

// WHY: Mock useQueryClient — page.tsx uses it to invalidate history cache after generation start
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query')
  return { ...actual, useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }) }
})

// WHY: Mock MediaHistoryTab — it uses useQuery internally which needs QueryClientProvider
vi.mock('@/app/video-gen/components/MediaHistoryTab', () => ({
  MediaHistoryTab: () => <div data-testid="media-history-tab">Historia mock</div>,
}))

import VideoGenPage from '@/app/video-gen/page'
import { MARKETPLACES } from '@/app/video-gen/components/MarketplaceSelector'

beforeEach(() => {
  vi.clearAllMocks()
  mockPost.mockReset()
  mockStartGeneration.mockReset()
})

describe('Kreator mediow AI — Video Mode', () => {
  it('renders page header with new branding', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Kreator mediow AI')).toBeInTheDocument()
    expect(screen.getByText('Generuj wideo produktowe lub infografiki A+ Content')).toBeInTheDocument()
  })

  it('shows media mode toggle (Wideo AI / Obrazy A+)', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Wideo AI')).toBeInTheDocument()
    expect(screen.getByText('Obrazy A+')).toBeInTheDocument()
  })

  it('shows page-level tabs (Generuj / Historia)', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Generuj')).toBeInTheDocument()
    expect(screen.getByText('Historia')).toBeInTheDocument()
  })

  it('defaults to video mode with URL input tab', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Link do produktu')).toBeInTheDocument()
    // WHY: "Wgraj zdjecie" appears in InputModeTabs — verify at least one exists
    expect(screen.getAllByText('Wgraj zdjecie').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Wybierz marketplace')).toBeInTheDocument()
  })

  it('renders all 10 marketplace buttons', () => {
    render(<VideoGenPage />)
    for (const mp of MARKETPLACES) {
      expect(screen.getByText(mp.label)).toBeInTheDocument()
    }
  })

  it('shows correct placeholder after selecting each marketplace', async () => {
    const user = userEvent.setup()
    render(<VideoGenPage />)

    for (const mp of MARKETPLACES) {
      await user.click(screen.getByText(mp.label))
      const input = screen.getByPlaceholderText(mp.placeholder)
      expect(input).toBeInTheDocument()
    }
  })

  it('generate button disabled when no URL entered', () => {
    render(<VideoGenPage />)
    const btn = screen.getByText('Generuj wideo AI')
    expect(btn.closest('button')).toBeDisabled()
  })

  it('generate button disabled without URL, enabled with URL (Amazon DE)', async () => {
    const user = userEvent.setup()
    render(<VideoGenPage />)

    const btn = screen.getByText('Generuj wideo AI')
    expect(btn.closest('button')).toBeDisabled()

    await user.click(screen.getByText('Amazon DE'))
    await user.type(screen.getByPlaceholderText('https://www.amazon.de/dp/B0...'), 'https://www.amazon.de/dp/B0TEST')
    expect(btn.closest('button')).not.toBeDisabled()
  })

  it('prompt section shows presets and textarea', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Opis ruchu')).toBeInTheDocument()
    expect(screen.getByText('product showcase')).toBeInTheDocument()
    expect(screen.getByText('zoom in')).toBeInTheDocument()
    expect(screen.getByText('floating product')).toBeInTheDocument()
    expect(screen.getByText('unboxing effect')).toBeInTheDocument()
  })

  it('clicking prompt preset updates textarea', async () => {
    const user = userEvent.setup()
    render(<VideoGenPage />)
    await user.click(screen.getByText('zoom in'))
    const textarea = screen.getByPlaceholderText(/product showcase, smooth rotation/)
    expect(textarea).toHaveValue('zoom in, dramatic lighting, dark background')
  })

  it('file upload mode hides marketplace, shows upload zone', async () => {
    const user = userEvent.setup()
    render(<VideoGenPage />)
    // WHY: "Wgraj zdjecie" appears in InputModeTabs AND HowItWorks section
    const uploadBtns = screen.getAllByText('Wgraj zdjecie')
    await user.click(uploadBtns[0])
    expect(screen.queryByText('Wybierz marketplace')).not.toBeInTheDocument()
    expect(screen.getByText('Zdjecie produktu')).toBeInTheDocument()
    expect(screen.getByText('Kliknij aby wybrac zdjecie')).toBeInTheDocument()
  })

  it('video output panel shows idle state', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Wynik')).toBeInTheDocument()
  })

  it('info sections render in video mode', () => {
    render(<VideoGenPage />)
    expect(screen.getByText('Jak to dziala — krok po kroku')).toBeInTheDocument()
  })
})


describe('Kreator mediow AI — Image Mode (Obrazy A+)', () => {
  async function switchToImageMode() {
    const user = userEvent.setup()
    render(<VideoGenPage />)
    await user.click(screen.getByText('Obrazy A+'))
    return user
  }

  it('switches to image mode and shows product form', async () => {
    await switchToImageMode()
    expect(screen.getByText('Dane produktu')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('np. Nike Air Max 90 Premium')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('np. Nike')).toBeInTheDocument()
  })

  it('hides marketplace selector and motion prompt in image mode', async () => {
    await switchToImageMode()
    expect(screen.queryByText('Wybierz marketplace')).not.toBeInTheDocument()
    expect(screen.queryByText('Opis ruchu')).not.toBeInTheDocument()
    expect(screen.queryByText('Link do produktu')).not.toBeInTheDocument()
  })

  it('shows theme picker with 3 options', async () => {
    await switchToImageMode()
    expect(screen.getByText('Styl grafik')).toBeInTheDocument()
    expect(screen.getByText('Premium (ciemny)')).toBeInTheDocument()
    expect(screen.getByText('Jasny')).toBeInTheDocument()
    expect(screen.getByText('Amazon (bialy)')).toBeInTheDocument()
  })

  it('generate button shows image text', async () => {
    await switchToImageMode()
    expect(screen.getByText('Generuj grafiki A+')).toBeInTheDocument()
  })

  it('generate button disabled without product name', async () => {
    await switchToImageMode()
    const btn = screen.getByText('Generuj grafiki A+')
    expect(btn.closest('button')).toBeDisabled()
  })

  it('generate button enabled with product name + brand', async () => {
    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Test Product Name')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'TestBrand')
    const btn = screen.getByText('Generuj grafiki A+')
    expect(btn.closest('button')).not.toBeDisabled()
  })

  it('product name too short (2 chars) keeps button disabled', async () => {
    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'AB')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'X')
    const btn = screen.getByText('Generuj grafiki A+')
    expect(btn.closest('button')).toBeDisabled()
  })

  // WHY: Image generation now uses background API (startGeneration) not apiClient.post
  it('calls startGeneration with correct payload on generate', async () => {
    mockStartGeneration.mockResolvedValue({ id: 42, status: 'pending' })

    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Buty Nike Air Max')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'Nike')
    await user.click(screen.getByText('Generuj grafiki A+'))

    await waitFor(() => {
      expect(mockStartGeneration).toHaveBeenCalledWith(
        expect.objectContaining({
          media_type: 'images',
          product_name: 'Buty Nike Air Max',
          brand: 'Nike',
          theme: 'dark_premium',
          llm_provider: 'beast',
        }),
      )
    })
  })

  it('registers background job after starting generation', async () => {
    mockStartGeneration.mockResolvedValue({ id: 99, status: 'pending' })

    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Test Product')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'Brand')
    await user.click(screen.getByText('Generuj grafiki A+'))

    await waitFor(() => {
      expect(mockAddJob).toHaveBeenCalledWith(99, 'images')
    })
  })

  it('shows toast on generation start', async () => {
    mockStartGeneration.mockResolvedValue({ id: 1, status: 'pending' })

    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Test Product')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'Brand')
    await user.click(screen.getByText('Generuj grafiki A+'))

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Generowanie rozpoczete' }),
      )
    })
  })

  it('shows error toast on API failure', async () => {
    mockStartGeneration.mockRejectedValue(new Error('Beast AI niedostepny'))

    const user = await switchToImageMode()
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Test Produkt')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'TestBrand')
    await user.click(screen.getByText('Generuj grafiki A+'))

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Blad uruchamiania generacji',
          description: 'Beast AI niedostepny',
          variant: 'destructive',
        }),
      )
    })
  })

  it('theme selection changes before generating', async () => {
    mockStartGeneration.mockResolvedValue({ id: 1, status: 'pending' })

    const user = await switchToImageMode()
    await user.click(screen.getByText('Amazon (bialy)'))
    await user.type(screen.getByPlaceholderText('np. Nike Air Max 90 Premium'), 'Test Product')
    await user.type(screen.getByPlaceholderText('np. Nike'), 'Brand')
    await user.click(screen.getByText('Generuj grafiki A+'))

    await waitFor(() => {
      expect(mockStartGeneration).toHaveBeenCalledWith(
        expect.objectContaining({ theme: 'amazon_white' }),
      )
    })
  })

  it('hides info sections in image mode', async () => {
    await switchToImageMode()
    expect(screen.queryByText('Jak to dziala — krok po kroku')).not.toBeInTheDocument()
  })

  it('bullet points textarea accepts multiline input', async () => {
    const user = await switchToImageMode()
    const textarea = screen.getByPlaceholderText(/Technologia Air Max/)
    await user.type(textarea, 'Cecha 1\nCecha 2\nCecha 3')
    expect(textarea).toHaveValue('Cecha 1\nCecha 2\nCecha 3')
  })
})


describe('Kreator mediow AI — Mode Switching', () => {
  it('switching modes resets state', async () => {
    const user = userEvent.setup()
    render(<VideoGenPage />)

    // Enter URL in video mode
    await user.click(screen.getByText('Amazon DE'))
    const urlInput = screen.getByPlaceholderText('https://www.amazon.de/dp/B0...')
    await user.type(urlInput, 'https://www.amazon.de/dp/B0TEST')

    // Switch to images
    await user.click(screen.getByText('Obrazy A+'))
    expect(screen.queryByText('Wybierz marketplace')).not.toBeInTheDocument()
    expect(screen.getByText('Dane produktu')).toBeInTheDocument()

    // Switch back to video
    await user.click(screen.getByText('Wideo AI'))
    expect(screen.getByText('Wybierz marketplace')).toBeInTheDocument()
  })
})


describe('Kreator mediow AI — Marketplace URL validation per marketplace', () => {
  const TEST_URLS: Record<string, string> = {
    amazon_de: 'https://www.amazon.de/dp/B0DFGBM7KP',
    amazon_com: 'https://www.amazon.com/dp/B0DFGBM7KP',
    amazon_co_uk: 'https://www.amazon.co.uk/dp/B0DFGBM7KP',
    amazon_pl: 'https://www.amazon.pl/dp/B0DFGBM7KP',
    allegro: 'https://allegro.pl/oferta/buty-nike-air-max-90-12345678',
    ebay: 'https://www.ebay.com/itm/123456789012',
    kaufland: 'https://www.kaufland.de/product/123456789/',
    rozetka: 'https://rozetka.com.ua/nike-air-max/p123456/',
    aliexpress: 'https://www.aliexpress.com/item/1005001234567.html',
    temu: 'https://www.temu.com/product-123.html',
  }

  for (const mp of MARKETPLACES) {
    it(`${mp.label}: URL input accepts valid URL and enables generate`, async () => {
      const user = userEvent.setup()
      const { unmount } = render(<VideoGenPage />)

      await user.click(screen.getByText(mp.label))
      const input = screen.getByPlaceholderText(mp.placeholder)
      await user.type(input, TEST_URLS[mp.id])

      expect(input).toHaveValue(TEST_URLS[mp.id])
      const btn = screen.getByText('Generuj wideo AI')
      expect(btn.closest('button')).not.toBeDisabled()

      unmount()
    })
  }
})
