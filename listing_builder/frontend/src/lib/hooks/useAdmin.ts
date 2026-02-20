// frontend/src/lib/hooks/useAdmin.ts
// Purpose: Check if current user is an admin (for conditional UI)
// NOT for: Enforcing security (backend does that via require_admin)

'use client'

import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api/client'

interface AdminMe {
  is_admin: boolean
  email: string
}

export function useAdmin() {
  const { data, isLoading } = useQuery<AdminMe>({
    queryKey: ['admin-me'],
    queryFn: async () => {
      const res = await apiRequest<AdminMe>('get', '/admin/me')
      if (res.error) return { is_admin: false, email: '' }
      return res.data!
    },
    // WHY: Admin status doesn't change mid-session — avoid unnecessary refetches
    staleTime: 5 * 60 * 1000,
  })

  return {
    isAdmin: data?.is_admin ?? false,
    isLoading,
  }
}
