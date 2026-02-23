// frontend/src/lib/__tests__/utils.test.ts
// Purpose: Tests for utility functions — cn, formatDate, truncate, status helpers, debounce
// NOT for: Component or API tests

import { describe, it, expect, vi } from 'vitest'
import {
  cn,
  formatDate,
  truncate,
  getStatusColor,
  getStatusLabel,
  debounce,
  formatRelativeTime,
  formatNumber,
  formatPrice,
  getScoreColor,
  sleep,
} from '../utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-2', 'py-1')).toBe('px-2 py-1')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('deduplicates Tailwind conflicts', () => {
    // WHY: tailwind-merge should pick the last conflicting class
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })
})

describe('formatDate', () => {
  it('formats a date string', () => {
    const result = formatDate('2024-06-15T10:30:00Z')
    expect(result).toContain('2024')
    expect(result).toContain('Jun')
  })

  it('accepts a Date object', () => {
    const result = formatDate(new Date('2024-01-01T00:00:00Z'))
    expect(result).toContain('2024')
  })
})

describe('formatRelativeTime', () => {
  it('returns "just now" for very recent', () => {
    const now = new Date()
    expect(formatRelativeTime(now)).toBe('just now')
  })

  it('returns minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60_000)
    expect(formatRelativeTime(fiveMinAgo)).toBe('5m ago')
  })

  it('returns hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600_000)
    expect(formatRelativeTime(twoHoursAgo)).toBe('2h ago')
  })

  it('returns days ago', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 86400_000)
    expect(formatRelativeTime(threeDaysAgo)).toBe('3d ago')
  })
})

describe('truncate', () => {
  it('returns short text unchanged', () => {
    expect(truncate('hello', 10)).toBe('hello')
  })

  it('truncates long text with ellipsis', () => {
    expect(truncate('hello world', 5)).toBe('hello...')
  })

  it('returns exact-length text unchanged', () => {
    expect(truncate('12345', 5)).toBe('12345')
  })
})

describe('formatNumber', () => {
  it('adds commas to large numbers', () => {
    expect(formatNumber(1234567)).toBe('1,234,567')
  })
})

describe('formatPrice', () => {
  it('formats USD by default', () => {
    const result = formatPrice(29.99)
    expect(result).toContain('29.99')
    expect(result).toContain('$')
  })

  it('formats other currencies', () => {
    const result = formatPrice(49, 'PLN')
    expect(result).toContain('49')
  })
})

describe('getStatusColor', () => {
  it('returns yellow for imported', () => {
    expect(getStatusColor('imported')).toContain('yellow')
  })

  it('returns blue for optimizing', () => {
    expect(getStatusColor('optimizing')).toContain('blue')
  })

  it('returns green for optimized', () => {
    expect(getStatusColor('optimized')).toContain('green')
  })

  it('returns red for failed', () => {
    expect(getStatusColor('failed')).toContain('red')
  })

  it('returns red for error', () => {
    expect(getStatusColor('error')).toContain('red')
  })

  it('returns gray for unknown status', () => {
    expect(getStatusColor('unknown')).toContain('gray')
  })
})

describe('getStatusLabel', () => {
  it('maps imported to Polish', () => {
    expect(getStatusLabel('imported')).toBe('Zaimportowany')
  })

  it('maps optimized to Polish', () => {
    expect(getStatusLabel('optimized')).toBe('Zoptymalizowany')
  })

  it('returns raw status for unknown', () => {
    expect(getStatusLabel('custom')).toBe('custom')
  })
})

describe('getScoreColor', () => {
  it('returns green for high scores', () => {
    expect(getScoreColor(85)).toContain('green')
  })

  it('returns yellow for medium scores', () => {
    expect(getScoreColor(65)).toContain('yellow')
  })

  it('returns red for low scores', () => {
    expect(getScoreColor(40)).toContain('red')
  })
})

describe('debounce', () => {
  it('delays function call', () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const debounced = debounce(fn, 300)

    debounced()
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })

  it('resets timer on subsequent calls', () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const debounced = debounce(fn, 300)

    debounced()
    vi.advanceTimersByTime(200)
    debounced()
    vi.advanceTimersByTime(200)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })
})

describe('sleep', () => {
  it('resolves after given ms', async () => {
    vi.useFakeTimers()
    const promise = sleep(100)
    vi.advanceTimersByTime(100)
    await promise
    vi.useRealTimers()
  })
})
