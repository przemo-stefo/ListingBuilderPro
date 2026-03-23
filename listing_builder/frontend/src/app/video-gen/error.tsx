'use client'
import SectionError from '@/components/SectionError'
export default function VideoGenError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <SectionError error={error} reset={reset} sectionName="Generator wideo" />
}
