// frontend/src/app/demo/amazon-pro/layout.tsx
// Purpose: Override metadata for demo pages — no OctoHelper branding
// NOT for: Layout structure (uses parent layout)

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Amazon Listing Optimizer — Demo',
  description: 'AI-powered Amazon listing optimization demo — PYROX AI',
}

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
