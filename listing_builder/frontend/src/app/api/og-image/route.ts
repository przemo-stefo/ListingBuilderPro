// frontend/src/app/api/og-image/route.ts
// Purpose: Server-side og:image extractor — fetches article URL and returns og:image
// NOT for: Image generation, AI, or anything Groq-related

import { NextRequest, NextResponse } from 'next/server'

// WHY: Block SSRF — reject internal/private IPs and non-http protocols
function isPrivateUrl(urlStr: string): boolean {
  try {
    const parsed = new URL(urlStr);
    if (!['http:', 'https:'].includes(parsed.protocol)) return true;
    const h = parsed.hostname.toLowerCase();
    if (h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0' || h === '::1' || h === '[::1]') return true;
    if (h.startsWith('10.') || h.startsWith('192.168.') || h.startsWith('169.254.')) return true;
    if (/^172\.(1[6-9]|2\d|3[01])\./.test(h)) return true;
    if (h.startsWith('fd') || h.startsWith('fe80')) return true;
    if (!h.includes('.')) return true; // no TLD = internal hostname
    return false;
  } catch { return true; }
}

// WHY: In-memory cache avoids re-fetching the same URL within 1 hour
const cache = new Map<string, { image: string | null; ts: number }>()
const CACHE_TTL = 60 * 60 * 1000 // 1 hour
// WHY: Cap cache size to prevent memory DoS from many unique URLs
const CACHE_MAX_SIZE = 500

// WHY: Google News RSS gives redirect URLs (news.google.com/rss/articles/CBMi...)
// that use JS redirects. We fetch the page and extract the real URL from
// <a> tags, data-url attributes, or canonical/redirect meta tags.
async function resolveGoogleNewsUrl(gnewsUrl: string): Promise<string | null> {
  try {
    const res = await fetch(gnewsUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      redirect: 'follow',
      signal: AbortSignal.timeout(5000),
    })
    // WHY: If Google News does a 302 redirect to the real article, res.url has it
    if (res.url && !res.url.includes('news.google.com') && !res.url.includes('consent.google')) {
      return res.url
    }
    const html = await res.text()
    // WHY: Google News page often has the real URL in data-n-au attribute or <a> tag
    const dataUrl = html.match(/data-n-au="([^"]+)"/)
    if (dataUrl) return dataUrl[1]
    // WHY: Sometimes it's in a <link rel="canonical"> or <meta http-equiv="refresh">
    const canonical = html.match(/<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']/i)
    if (canonical && !canonical[1].includes('news.google.com')) return canonical[1]
    const refresh = html.match(/url=([^"'\s>]+)/i)
    if (refresh && refresh[1].startsWith('http') && !refresh[1].includes('google.com')) return refresh[1]
    return null
  } catch {
    return null
  }
}

async function fetchWithSsrfCheck(url: string): Promise<Response | null> {
  // WHY: Manual redirect handling — each hop checked against private IP list
  let currentUrl = url
  for (let hops = 0; hops < 5; hops++) {
    const res = await fetch(currentUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)',
        'Accept': 'text/html',
      },
      redirect: 'manual',
      signal: AbortSignal.timeout(5000),
    })
    if (res.status >= 300 && res.status < 400) {
      const location = res.headers.get('location')
      if (!location) return null
      // WHY: Resolve relative redirects against current URL
      const nextUrl = new URL(location, currentUrl).toString()
      if (isPrivateUrl(nextUrl)) return null
      currentUrl = nextUrl
      continue
    }
    return res
  }
  return null // too many redirects
}

async function fetchOgImage(url: string): Promise<string | null> {
  const res = await fetchWithSsrfCheck(url)
  if (!res || !res.ok) return null

  // WHY: Only read first 50KB — og:image is always in <head>
  const reader = res.body?.getReader()
  let html = ''
  if (reader) {
    const decoder = new TextDecoder()
    let bytesRead = 0
    while (bytesRead < 50_000) {
      const { done, value } = await reader.read()
      if (done) break
      html += decoder.decode(value, { stream: true })
      bytesRead += value.length
    }
    reader.cancel()
  }

  const match = html.match(
    /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i
  ) || html.match(
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i
  )
  return match?.[1] || null
}

export async function GET(request: NextRequest) {
  const url = request.nextUrl.searchParams.get('url')
  if (!url) {
    return NextResponse.json({ image: null }, { status: 400 })
  }

  // WHY: SSRF protection — block requests to internal/private networks
  if (isPrivateUrl(url)) {
    return NextResponse.json({ image: null }, { status: 400 })
  }

  const cached = cache.get(url)
  if (cached && Date.now() - cached.ts < CACHE_TTL) {
    return NextResponse.json({ image: cached.image })
  }

  try {
    let image: string | null = null
    const isGoogleNews = url.includes('news.google.com/rss/articles/')

    if (isGoogleNews) {
      // WHY: Google News URLs need 2-step resolution: resolve redirect → fetch og:image
      const realUrl = await resolveGoogleNewsUrl(url)
      // WHY: SSRF check on resolved URL — attacker could use Google News redirect to reach internal IPs
      if (realUrl && !isPrivateUrl(realUrl)) {
        image = await fetchOgImage(realUrl)
      }
    } else {
      image = await fetchOgImage(url)
    }

    // WHY: Evict oldest entries when cache is full — simple FIFO keeps memory bounded
    if (cache.size >= CACHE_MAX_SIZE) {
      const oldest = cache.keys().next().value!
      cache.delete(oldest)
    }
    cache.set(url, { image, ts: Date.now() })
    return NextResponse.json({ image })
  } catch {
    cache.set(url, { image: null, ts: Date.now() })
    return NextResponse.json({ image: null })
  }
}
