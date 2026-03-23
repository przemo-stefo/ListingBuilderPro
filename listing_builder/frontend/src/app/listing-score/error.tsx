'use client'
import SectionError from '@/components/SectionError'
export default function ListingScoreError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Listing Score" />
}
