// frontend/src/app/optimize/components/FeedbackWidget.tsx
// Purpose: Star rating feedback widget — stored in listing_history for self-learning loop
// NOT for: Other result display components

'use client'

import { useState } from 'react'
import { Star } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export function FeedbackWidget({
  listingHistoryId,
}: {
  listingHistoryId: string | null | undefined
}) {
  const [rating, setRating] = useState<number>(0)
  const [hovered, setHovered] = useState<number>(0)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!listingHistoryId) return null

  async function submitFeedback(stars: number) {
    setRating(stars)
    setError(null)
    try {
      const res = await fetch(`/api/proxy/optimizer/history/${listingHistoryId}/feedback`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: stars }),
      })
      if (!res.ok) throw new Error('Failed to submit')
      setSubmitted(true)
    } catch {
      setError('Nie udalo sie zapisac oceny')
    }
  }

  return (
    <Card>
      <CardContent className="flex items-center justify-between py-4">
        <div>
          <p className="text-sm font-medium text-gray-300">
            {submitted ? 'Dzieki za ocene!' : 'Ocen ten listing'}
          </p>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </div>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => !submitted && submitFeedback(star)}
              onMouseEnter={() => !submitted && setHovered(star)}
              onMouseLeave={() => setHovered(0)}
              disabled={submitted}
              className="transition-colors disabled:cursor-default"
            >
              <Star
                className={cn(
                  'h-6 w-6',
                  (hovered || rating) >= star
                    ? 'fill-amber-400 text-amber-400'
                    : 'text-gray-600'
                )}
              />
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
