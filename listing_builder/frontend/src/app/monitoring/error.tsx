'use client'
import SectionError from '@/components/SectionError'
export default function MonitoringError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Monitoring" />
}
