/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // API backend URL
  env: {
    // Empty string = use Next.js API routes; set env var to point to external backend
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
}

module.exports = nextConfig
