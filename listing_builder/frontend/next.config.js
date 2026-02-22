// frontend/next.config.js
// Purpose: Next.js configuration for Marketplace Listing Automation frontend
// NOT for: Backend configuration or API settings

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
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
}

module.exports = nextConfig
