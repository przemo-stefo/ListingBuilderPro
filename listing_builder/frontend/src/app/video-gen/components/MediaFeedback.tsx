// frontend/src/app/video-gen/components/MediaFeedback.tsx
// Purpose: Feedback form for media generation — user notes what to improve
// NOT for: History listing or generation logic

'use client'

import { useState } from 'react'
import { Loader2, Send, X } from 'lucide-react'
import { saveFeedback } from '@/lib/api/mediaGeneration'
import { useToast } from '@/lib/hooks/useToast'
import { useQueryClient } from '@tanstack/react-query'

interface Props {
  genId: number
  existingFeedback: string
  onClose: () => void
}

export function MediaFeedback({ genId, existingFeedback, onClose }: Props) {
  const [text, setText] = useState(existingFeedback)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const handleSave = async () => {
    if (!text.trim()) return
    setSaving(true)
    try {
      await saveFeedback(genId, text.trim())
      toast({ title: 'Feedback zapisany' })
      queryClient.invalidateQueries({ queryKey: ['media-history'] })
      onClose()
    } catch (err) {
      toast({
        title: 'Blad zapisu',
        description: (err as Error).message,
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-white">Feedback — co poprawic?</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="np. Za ciemne tlo, dodaj wiecej cech produktu, zmien ukklad na poziomy..."
        className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
      />
      <p className="text-[10px] text-gray-600">
        System uczy sie z Twojego feedbacku — przyszle generacje beda lepiej dopasowane.
      </p>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !text.trim()}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Zapisz feedback
        </button>
        <button
          onClick={onClose}
          className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 transition-colors"
        >
          Anuluj
        </button>
      </div>
    </div>
  )
}
