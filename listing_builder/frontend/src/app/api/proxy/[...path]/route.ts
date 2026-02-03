// frontend/src/app/api/proxy/[...path]/route.ts
// Purpose: Server-side proxy to backend API — keeps API key out of client bundle
// NOT for: Direct business logic or data processing

import { NextRequest, NextResponse } from 'next/server'

// Server-only env var (no NEXT_PUBLIC_ prefix = never sent to browser)
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const API_KEY = process.env.API_KEY || ''

async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join('/')
  const url = new URL(`/api/${path}`, BACKEND_URL)

  // Forward query params (except cache-busting _t)
  request.nextUrl.searchParams.forEach((value, key) => {
    if (key !== '_t') url.searchParams.set(key, value)
  })

  // Build headers — inject API key server-side
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  }

  // Forward webhook secret if present (for import endpoints)
  const webhookSecret = request.headers.get('X-Webhook-Secret')
  if (webhookSecret) {
    headers['X-Webhook-Secret'] = webhookSecret
  }

  // Forward request body for non-GET methods
  let body: string | undefined
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    try {
      body = await request.text()
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

    const data = await response.text()

    return new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
      },
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
