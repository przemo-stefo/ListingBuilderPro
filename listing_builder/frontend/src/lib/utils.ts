// frontend/src/lib/utils.ts
// Purpose: Utility functions for class names, formatting, and common operations
// NOT for: Business logic or API calls

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Merge Tailwind classes safely
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format date to readable string
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Format relative time (e.g., "2 hours ago")
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return formatDate(d)
}

// Truncate text with ellipsis
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

// Format number with commas
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

// Format price
export function formatPrice(price: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(price)
}

// Get status color class
export function getStatusColor(status: string): string {
  switch (status) {
    case 'pending':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'optimized':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    case 'published':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'error':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

// Get optimization score color
export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

// Debounce function for search inputs
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// Sleep utility for polling
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
