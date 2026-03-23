'use client'
import SectionError from '@/components/SectionError'
export default function ComplianceError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Compliance Guard" />
}
