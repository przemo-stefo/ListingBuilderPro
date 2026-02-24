// frontend/src/app/api/proxy/[...path]/route.ts
// Purpose: Server-side proxy to backend API — keeps API key out of client bundle
// NOT for: Direct business logic or data processing

import { NextRequest, NextResponse } from 'next/server'

// Server-only env var (no NEXT_PUBLIC_ prefix = never sent to browser)
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const API_KEY = process.env.API_KEY || ''

// WHY: Allowlist prevents the proxy from being an open relay to arbitrary backend paths
const ALLOWED_PATH_PREFIXES = [
  'optimizer/generate',
  'optimizer/history',
  'optimizer/health',
  'optimizer/traces',
  'optimizer/grey-market-score',
  'knowledge/chat',
  'knowledge/stats',
  'products',
  'compliance',
  'converter',
  'import',
  'export',
  'settings',
  'quiz',
  'monitoring',
  'listings',
  'keywords',
  'analytics',
  'competitors',
  'inventory',
  'keepa',
  'epr',
  'oauth',
  'stripe',
  'news',
  'allegro',
  'research',
  'auth',
  'admin',
  'alert-settings',
  'ads',
  'score',
]

// WHY: Block destructive methods on sensitive endpoints — defense in depth
const BLOCKED_METHODS: Record<string, string[]> = {
  'import/webhook': ['DELETE', 'PUT', 'PATCH'],
  'settings': ['DELETE'],
  'admin': ['DELETE', 'PUT'],
  'oauth': ['PUT', 'PATCH'],
  'stripe/webhook': ['DELETE', 'PUT', 'PATCH'],
}

async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join('/')

  // Security: only allow known API paths
  const isAllowed = ALLOWED_PATH_PREFIXES.some(prefix => path.startsWith(prefix))
  if (!isAllowed) {
    return NextResponse.json({ detail: 'Forbidden: path not allowed' }, { status: 403 })
  }

  // Security: block destructive methods on sensitive paths
  for (const [blockedPath, methods] of Object.entries(BLOCKED_METHODS)) {
    if (path.startsWith(blockedPath) && methods.includes(request.method)) {
      return NextResponse.json({ detail: 'Method not allowed' }, { status: 405 })
    }
  }

  const url = new URL(`/api/${path}`, BACKEND_URL)

  // Forward query params (except cache-busting _t)
  request.nextUrl.searchParams.forEach((value, key) => {
    if (key !== '_t') url.searchParams.set(key, value)
  })

  // WHY: Multipart requests (file uploads) need the original Content-Type with boundary string
  const incomingContentType = request.headers.get('Content-Type') || ''
  const isMultipart = incomingContentType.startsWith('multipart/form-data')

  // Build headers — inject API key server-side
  const headers: Record<string, string> = {
    'Content-Type': isMultipart ? incomingContentType : 'application/json',
    'X-API-Key': API_KEY,
  }

  // WHY: Forward JWT so backend can identify the user (Supabase Auth)
  const authHeader = request.headers.get('Authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }

  // Forward webhook secret if present (for import endpoints)
  const webhookSecret = request.headers.get('X-Webhook-Secret')
  if (webhookSecret) {
    headers['X-Webhook-Secret'] = webhookSecret
  }

  // WHY: Forward license key for backend premium tier enforcement
  const licenseKey = request.headers.get('X-License-Key')
  if (licenseKey) {
    headers['X-License-Key'] = licenseKey
  }

  // Forward request body for non-GET methods
  // WHY: Multipart bodies must stay as raw bytes — text() would corrupt binary file data
  let body: BodyInit | undefined
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    try {
      body = isMultipart
        ? new Uint8Array(await request.arrayBuffer())
        : await request.text()
    } catch {
      // No body — that's fine
    }
  }

  try {
    const response = await fetch(url.toString(), {
      method: request.method,
      headers,
      body,
    })

    // WHY: Use arrayBuffer for binary responses (file downloads), text for JSON
    const contentDisposition = response.headers.get('Content-Disposition')
    const responseHeaders: Record<string, string> = {
      'Content-Type': response.headers.get('Content-Type') || 'application/json',
    }
    if (contentDisposition) {
      responseHeaders['Content-Disposition'] = contentDisposition
    }

    const data = contentDisposition
      ? Buffer.from(await response.arrayBuffer())
      : await response.text()

    return new NextResponse(data, {
      status: response.status,
      headers: responseHeaders,
    })
  } catch (error) {
    return NextResponse.json(
      { detail: 'Backend unavailable' },
      { status: 502 }
    )
  }
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params)
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params)
}

export async function PUT(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params)
}

export async function DELETE(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params)
}

export async function PATCH(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyRequest(request, context.params)
}
