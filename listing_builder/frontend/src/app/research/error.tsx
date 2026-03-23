'use client'
import SectionError from '@/components/SectionError'
export default function ResearchError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Research" />
}
