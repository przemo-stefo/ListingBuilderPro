// frontend/next.config.js
// Purpose: Next.js configuration for Marketplace Listing Automation frontend
// NOT for: Backend configuration or API settings

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
    remotePatterns: [
      { protocol: 'https', hostname: '*.allegrostatic.com' },
      { protocol: 'https', hostname: 'images-na.ssl-images-amazon.com' },
      { protocol: 'https', hostname: '*.supabase.co' },
      { protocol: 'https', hostname: 'm.media-amazon.com' },
      { protocol: 'https', hostname: '*.ssl-images-amazon.com' },
    ],
  },
  // Enable standalone output for production
  output: 'standalone',
  // Rewrite /health → /api/health so monitoring bots can hit the root path
  async rewrites() {
    return [
      { source: '/health', destination: '/api/health' },
    ];
  },
  // WHY: Security headers — CSP omitted to avoid breaking Tailwind/Next.js inline styles
  async headers() {
    return [{
      source: '/:path*',
      headers: [
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
      ],
    }];
  },
}

module.exports = nextConfig
