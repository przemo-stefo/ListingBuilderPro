// frontend/src/components/providers/__tests__/AuthGuard.test.tsx
// Purpose: Tests for AuthGuard — route protection, public paths, loading state
// NOT for: Auth logic (that's AuthProvider)

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthGuard } from '../AuthGuard'
import { setMockPathname, mockReplace } from '@/__tests__/setup'

// WHY: Mock useAuth separately so each test controls user/loading state
const mockUseAuth = vi.fn()
vi.mock('../AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}))

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockPathname('/')
  })

  it('renders children on public path when not logged in', () => {
    setMockPathname('/login')
    mockUseAuth.mockReturnValue({ user: null, loading: false })

    render(<AuthGuard><div>Login Page</div></AuthGuard>)
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('renders children on public prefix path', () => {
    setMockPathname('/payment/success')
    mockUseAuth.mockReturnValue({ user: null, loading: false })

    render(<AuthGuard><div>Payment</div></AuthGuard>)
    expect(screen.getByText('Payment')).toBeInTheDocument()
  })

  it('renders children when user is authenticated', () => {
    setMockPathname('/dashboard')
    mockUseAuth.mockReturnValue({ user: { id: '1' }, loading: false })

    render(<AuthGuard><div>Dashboard</div></AuthGuard>)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('redirects to /login when not authenticated on protected path', () => {
    setMockPathname('/dashboard')
    mockUseAuth.mockReturnValue({ user: null, loading: false })

    render(<AuthGuard><div>Dashboard</div></AuthGuard>)
    expect(mockReplace).toHaveBeenCalledWith('/login')
  })

  it('shows loading spinner on protected path while loading', () => {
    setMockPathname('/dashboard')
    mockUseAuth.mockReturnValue({ user: null, loading: true })

    const { container } = render(<AuthGuard><div>Dashboard</div></AuthGuard>)
    // WHY: Loading spinner has animate-spin class
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })

  it('renders public page even while loading', () => {
    setMockPathname('/login')
    mockUseAuth.mockReturnValue({ user: null, loading: true })

    render(<AuthGuard><div>Login</div></AuthGuard>)
    expect(screen.getByText('Login')).toBeInTheDocument()
  })

  it('does not render protected content when user is null', () => {
    setMockPathname('/settings')
    mockUseAuth.mockReturnValue({ user: null, loading: false })

    const { container } = render(<AuthGuard><div>Settings</div></AuthGuard>)
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
  })
})
