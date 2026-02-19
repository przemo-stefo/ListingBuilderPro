// frontend/src/app/integrations/page.tsx
// Purpose: Centralized marketplace integrations — OAuth connect/disconnect for all marketplaces
// NOT for: Compliance-specific scanning or monitoring logic

'use client'

import { Suspense } from 'react'
import IntegrationsTab from '@/app/compliance/components/IntegrationsTab'

// WHY: No extra header — IntegrationsTab already renders "Integracje Marketplace" h2 + description
export default function IntegrationsPage() {
  return (
    <Suspense>
      <IntegrationsTab />
    </Suspense>
  )
}
