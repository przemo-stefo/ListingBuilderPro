// frontend/src/app/auth/callback/route.ts
// Purpose: PKCE code exchange for Supabase Auth (email links: confirm, reset password)
// NOT for: Login/signup UI or session management

import { NextResponse, type NextRequest } from 'next/server'
import { createServerClient } from '@supabase/ssr'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'

  // WHY: Default redirect — if code exchange fails, send to login
  const fallback = `${origin}/login`

  if (!code) {
    return NextResponse.redirect(fallback)
  }

  // WHY: Create response FIRST so we can set cookies on it during exchange
  const redirectUrl = `${origin}${next}`
  const response = NextResponse.redirect(redirectUrl)

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options)
          })
        },
      },
    }
  )

  const { error } = await supabase.auth.exchangeCodeForSession(code)

  if (error) {
    return NextResponse.redirect(fallback)
  }

  return response
}
