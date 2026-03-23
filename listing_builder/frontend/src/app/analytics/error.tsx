'use client'
import SectionError from '@/components/SectionError'
export default function AnalyticsError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Analityka" />
}
