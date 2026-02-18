// frontend/src/lib/supabase.ts
// Purpose: Supabase browser client for auth (login, signup, session)
// NOT for: Server-side operations or database queries

import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
