// frontend/src/__tests__/setup.ts
// Purpose: Global test setup — jest-dom matchers, mock next/navigation, mock supabase
// NOT for: Individual test logic

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock next/navigation — used by AuthGuard and FeatureGate
const mockPush = vi.fn()
const mockReplace = vi.fn()
let mockPathname = '/'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => mockPathname,
  useSearchParams: () => new URLSearchParams(),
}))

// WHY: Export so tests can change pathname and assert on router calls
export { mockPush, mockReplace }
export function setMockPathname(p: string) {
  mockPathname = p
}

// Mock supabase client — AuthProvider uses createClient()
vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn().mockResolvedValue({ error: null }),
      signUp: vi.fn().mockResolvedValue({ error: null }),
      signOut: vi.fn().mockResolvedValue({}),
      resetPasswordForEmail: vi.fn().mockResolvedValue({ error: null }),
    },
  }),
}))
