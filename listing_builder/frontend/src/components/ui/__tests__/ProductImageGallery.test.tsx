// frontend/src/components/ui/__tests__/ProductImageGallery.test.tsx
// Purpose: Tests for ProductImageGallery — empty state, single image, thumbnails
// NOT for: Image upload or optimization logic

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ProductImageGallery from '../ProductImageGallery'

describe('ProductImageGallery', () => {
  it('shows placeholder icon when images array is empty', () => {
    const { container } = render(<ProductImageGallery images={[]} />)
    // WHY: Lucide ImageIcon renders as SVG
    expect(container.querySelector('svg')).toBeInTheDocument()
    expect(container.querySelectorAll('img')).toHaveLength(0)
  })

  it('renders single image without thumbnails', () => {
    const { container } = render(
      <ProductImageGallery images={['https://example.com/img1.jpg']} />
    )

    // WHY: alt="" gives role=presentation, so use querySelectorAll
    const images = container.querySelectorAll('img')
    expect(images).toHaveLength(1)
    expect(images[0]).toHaveAttribute('src', 'https://example.com/img1.jpg')

    // No thumbnail buttons for single image
    expect(screen.queryAllByRole('button')).toHaveLength(0)
  })

  it('renders thumbnails for multiple images', () => {
    const urls = [
      'https://example.com/img1.jpg',
      'https://example.com/img2.jpg',
      'https://example.com/img3.jpg',
    ]

    const { container } = render(<ProductImageGallery images={urls} />)

    // Primary + 3 thumbnails = 4 img elements
    const images = container.querySelectorAll('img')
    expect(images).toHaveLength(4)

    // 3 thumbnail buttons
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(3)
  })

  it('changes primary image on thumbnail click', () => {
    const urls = [
      'https://example.com/img1.jpg',
      'https://example.com/img2.jpg',
    ]

    const { container } = render(<ProductImageGallery images={urls} />)

    // WHY: First image in DOM is the primary display image
    const primaryBefore = container.querySelectorAll('img')[0]
    expect(primaryBefore).toHaveAttribute('src', urls[0])

    // Click second thumbnail button
    const buttons = screen.getAllByRole('button')
    fireEvent.click(buttons[1])

    // Primary image should now show second URL
    const primaryAfter = container.querySelectorAll('img')[0]
    expect(primaryAfter).toHaveAttribute('src', urls[1])
  })

  it('highlights active thumbnail with white border', () => {
    const urls = ['https://example.com/a.jpg', 'https://example.com/b.jpg']

    render(<ProductImageGallery images={urls} />)

    const buttons = screen.getAllByRole('button')
    // WHY: First thumbnail is active by default
    expect(buttons[0].className).toContain('border-white')
    expect(buttons[1].className).not.toContain('border-white')
  })
})
